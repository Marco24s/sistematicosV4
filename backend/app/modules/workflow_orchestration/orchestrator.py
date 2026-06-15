from typing import Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.domain.exceptions import DomainError
from app.modules.workflow_orchestration.domain.models import WorkflowInstance, WorkflowTransitionLog, WorkflowStatus, RepairCycleState
from app.modules.workflow_orchestration.domain.commands import (
    CreateMaintenanceRequestCommand,
    CreateQualityInspectionCommand,
    CreateServiceReleaseCommand,
    UpdateTechnicalHistoryCommand,
    UpdateServiceStatusCommand,
    CreateStockAvailabilityCommand,
    BlockAircraftCommand
)
from app.shared.events.bus import command_bus


class RepairCycleOrchestrator:
    # Máquina de estados con transiciones válidas
    VALID_TRANSITIONS = {
        RepairCycleState.FAILURE_DETECTED: [RepairCycleState.REQUEST_CREATED],
        RepairCycleState.REQUEST_CREATED: [RepairCycleState.REPAIR_ASSIGNED],
        RepairCycleState.REPAIR_ASSIGNED: [RepairCycleState.UNDER_REPAIR],
        RepairCycleState.UNDER_REPAIR: [RepairCycleState.QUALITY_PENDING],
        RepairCycleState.QUALITY_PENDING: [RepairCycleState.SERVICE_RELEASED],
        RepairCycleState.SERVICE_RELEASED: [RepairCycleState.STOCK_AVAILABLE],
        RepairCycleState.STOCK_AVAILABLE: [RepairCycleState.COMPLETED]
    }

    def start(self, correlation_id: UUID, session: Session) -> WorkflowInstance:
        # Validar si ya existe una instancia para este correlation_id
        stmt = select(WorkflowInstance).where(WorkflowInstance.correlation_id == correlation_id)
        instance = session.scalars(stmt).first()
        if instance:
            return instance

        instance = WorkflowInstance(
            workflow_type="RepairCycle",
            correlation_id=correlation_id,
            current_state=RepairCycleState.FAILURE_DETECTED,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        session.add(instance)
        session.flush()

        log = WorkflowTransitionLog(
            workflow_instance_id=instance.id,
            from_state="NONE",
            to_state=RepairCycleState.FAILURE_DETECTED,
            timestamp=datetime.now(timezone.utc),
            notes="Workflow started automatically"
        )
        session.add(log)
        session.flush()
        return instance

    def transition(
        self,
        instance: WorkflowInstance,
        to_state: RepairCycleState,
        session: Session,
        performed_by: str | None = None,
        notes: str | None = None
    ) -> WorkflowTransitionLog:
        current = instance.current_state
        allowed = self.VALID_TRANSITIONS.get(current, [])

        if to_state not in allowed:
            raise DomainError(f"Invalid transition from {current} to {to_state}")

        instance.current_state = to_state
        log = WorkflowTransitionLog(
            workflow_instance_id=instance.id,
            from_state=current,
            to_state=to_state,
            timestamp=datetime.now(timezone.utc),
            performed_by=performed_by,
            notes=notes
        )
        session.add(log)
        session.flush()

        # Emitir comandos basados en las transiciones de estado de coordinación
        if to_state == RepairCycleState.REQUEST_CREATED:
            cmd = CreateMaintenanceRequestCommand(
                payload={"asset_id": str(instance.correlation_id), "priority": "CRITICAL"}
            )
            command_bus.dispatch(cmd, session)
        elif to_state == RepairCycleState.QUALITY_PENDING:
            cmd = CreateQualityInspectionCommand(
                payload={"repair_task_id": str(instance.id)} # Ref al workflow
            )
            command_bus.dispatch(cmd, session)
        elif to_state == RepairCycleState.SERVICE_RELEASED:
            cmd = CreateServiceReleaseCommand(
                payload={"asset_id": str(instance.correlation_id), "inspection_id": str(instance.id)}
            )
            command_bus.dispatch(cmd, session)
        elif to_state == RepairCycleState.STOCK_AVAILABLE:
            cmd = CreateStockAvailabilityCommand(
                payload={"asset_id": str(instance.correlation_id), "location_id": str(instance.id)}
            )
            command_bus.dispatch(cmd, session)

        return log

    def complete(self, instance: WorkflowInstance, session: Session) -> WorkflowInstance:
        instance.current_state = RepairCycleState.COMPLETED
        instance.status = WorkflowStatus.COMPLETED
        instance.completed_at = datetime.now(timezone.utc)
        session.flush()
        return instance

    def fail(self, instance: WorkflowInstance, session: Session, reason: str) -> WorkflowInstance:
        instance.status = WorkflowStatus.FAILED
        instance.completed_at = datetime.now(timezone.utc)
        log = WorkflowTransitionLog(
            workflow_instance_id=instance.id,
            from_state=instance.current_state,
            to_state="FAILED",
            timestamp=datetime.now(timezone.utc),
            notes=f"Workflow failed: {reason}"
        )
        session.add(log)
        session.flush()
        return instance

    def cancel(self, instance: WorkflowInstance, session: Session) -> WorkflowInstance:
        instance.status = WorkflowStatus.CANCELED
        instance.completed_at = datetime.now(timezone.utc)
        session.flush()
        return instance

    def get_instance(self, correlation_id: UUID, session: Session) -> WorkflowInstance | None:
        stmt = select(WorkflowInstance).where(WorkflowInstance.correlation_id == correlation_id)
        return session.scalars(stmt).first()
