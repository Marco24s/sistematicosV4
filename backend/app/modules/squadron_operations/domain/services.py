from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.arsenal_workflow.domain.models import AuditEvent
from app.modules.assets.domain.models import Asset, TechnicalHistory
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.modules.squadron_operations.domain.models import (
    AircraftConfiguration,
    AircraftInspectionProgram,
    AircraftInspectionStatus,
    AirworthinessBlock,
    AirworthinessBlockSeverity,
    MaintenanceAction,
    MaintenanceActionStatus,
    MountedComponent,
    MountedComponentStatus,
    SquadronInventoryMovement,
    SquadronInventoryMovementType,
    SquadronQualityApproval,
    SquadronQualityApprovalStatus,
    StatisticalControlRecord,
    StatisticalControlStatus,
)
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class AuditedResult:
    entity: object
    audit_event: AuditEvent


class SquadronOperationsService:
    def install_component_on_aircraft(
        self,
        aircraft_configuration: AircraftConfiguration,
        component_asset: Asset,
        component_history: TechnicalHistory,
        position_code: str,
        installation_date: datetime,
        installed_by: str,
        actor_id: str,
    ) -> AuditedResult:
        if component_history.asset_id != component_asset.id:
            raise DomainError("Component technical history does not match component asset.")

        mounted_component = MountedComponent(
            id=uuid4(),
            aircraft_configuration_id=aircraft_configuration.id,
            asset_id=component_asset.id,
            position_code=position_code,
            installation_date=installation_date,
            installed_by=installed_by,
            status=MountedComponentStatus.ACTIVE,
        )
        component_history.notes = self._append_note(
            component_history.notes,
            f"Installed on aircraft {aircraft_configuration.aircraft_asset_id} at {position_code}.",
        )

        return self._result(
            mounted_component,
            actor_id,
            "instalo componente en aeronave",
            before_state={"technical_history_notes": component_history.notes},
            after_state={
                "mounted_component": self._mounted_component_state(mounted_component),
                "aircraft_configuration_id": str(aircraft_configuration.id),
            },
        )

    def remove_component_from_aircraft(
        self,
        mounted_component: MountedComponent,
        component_history: TechnicalHistory,
        removed_by: str,
        removed_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        if mounted_component.status != MountedComponentStatus.ACTIVE:
            raise DomainError("Only an active mounted component can be removed.")
        if component_history.asset_id != mounted_component.asset_id:
            raise DomainError("Component technical history does not match mounted component.")

        before_state = self._mounted_component_state(mounted_component)
        mounted_component.status = MountedComponentStatus.REMOVED
        component_history.notes = self._append_note(
            component_history.notes,
            f"Removed by {removed_by} at {removed_at.isoformat()}.",
        )
        return self._result(
            mounted_component,
            actor_id,
            "desmonto componente de aeronave",
            before_state=before_state,
            after_state={
                "mounted_component": self._mounted_component_state(mounted_component),
                "technical_history_notes": component_history.notes,
            },
        )

    def register_maintenance_action(
        self,
        aircraft_asset_id: UUID,
        performed_by: str,
        action_type: str,
        description: str,
        performed_at: datetime,
        requires_quality_approval: bool,
        actor_id: str,
    ) -> AuditedResult:
        action = MaintenanceAction(
            id=uuid4(),
            aircraft_asset_id=aircraft_asset_id,
            performed_by=performed_by,
            action_type=action_type,
            description=description,
            performed_at=performed_at,
            requires_quality_approval=requires_quality_approval,
            status=MaintenanceActionStatus.WAITING_QUALITY if requires_quality_approval else MaintenanceActionStatus.COMPLETED,
        )
        return self._result(
            action,
            actor_id,
            "registro tarea de mantenimiento escuadrilla",
            before_state=None,
            after_state=self._maintenance_action_state(action),
        )

    def approve_maintenance_action(
        self,
        maintenance_action: MaintenanceAction,
        inspector_id: UUID,
        approved: bool,
        notes: str | None,
        approved_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        if not maintenance_action.requires_quality_approval:
            raise DomainError("Maintenance action does not require quality approval.")

        before_state = self._maintenance_action_state(maintenance_action)
        approval = SquadronQualityApproval(
            id=uuid4(),
            maintenance_action_id=maintenance_action.id,
            inspector_id=inspector_id,
            approved=approved,
            notes=notes,
            approved_at=approved_at,
            status=SquadronQualityApprovalStatus.APPROVED if approved else SquadronQualityApprovalStatus.REJECTED,
        )
        maintenance_action.status = MaintenanceActionStatus.COMPLETED if approved else MaintenanceActionStatus.PENDING
        return self._result(
            approval,
            actor_id,
            "aprobo tarea de mantenimiento escuadrilla" if approved else "rechazo tarea de mantenimiento escuadrilla",
            before_state=before_state,
            after_state={
                "quality_approval": self._quality_approval_state(approval),
                "maintenance_action": self._maintenance_action_state(maintenance_action),
            },
        )

    def update_statistical_control(
        self,
        record: StatisticalControlRecord,
        technical_history: TechnicalHistory,
        maintenance_counters: list[MaintenanceCounter],
        warning_threshold: int,
        actor_id: str,
    ) -> AuditedResult:
        if record.asset_id != technical_history.asset_id:
            raise DomainError("Statistical record and technical history must refer to the same asset.")

        before_state = self._statistical_record_state(record)
        record.current_hours = Decimal(technical_history.current_total_hours)
        record.current_cycles = technical_history.current_total_cycles
        record.calendar_expiration = technical_history.calendar_expiration

        hour_counters = [counter for counter in maintenance_counters if counter.remaining_usage is not None]
        if hour_counters:
            record.remaining_hours = Decimal(min(counter.remaining_usage for counter in hour_counters))
            record.remaining_cycles = min(counter.remaining_usage for counter in hour_counters)

        today = date.today()
        if record.calendar_expiration and record.calendar_expiration <= today:
            record.status = StatisticalControlStatus.GROUNDING_REQUIRED
        elif record.remaining_hours is not None and record.remaining_hours <= 0:
            record.status = StatisticalControlStatus.OVERDUE
        elif record.remaining_hours is not None and record.remaining_hours <= warning_threshold:
            record.status = StatisticalControlStatus.WARNING
        else:
            record.status = StatisticalControlStatus.NORMAL

        return self._result(
            record,
            actor_id,
            "actualizo control estadistico",
            before_state=before_state,
            after_state=self._statistical_record_state(record),
        )

    def evaluate_operational_readiness(
        self,
        aircraft_asset_id: UUID,
        inspection_programs: list[AircraftInspectionProgram],
        statistical_records: list[StatisticalControlRecord],
        maintenance_counters: list[MaintenanceCounter],
        actor_id: str,
    ) -> list[AuditedResult]:
        blocks: list[AuditedResult] = []
        today = date.today()

        for inspection in inspection_programs:
            if inspection.status == AircraftInspectionStatus.OVERDUE or (inspection.next_due and inspection.next_due <= today):
                inspection.status = AircraftInspectionStatus.OVERDUE
                blocks.append(
                    self._block(
                        aircraft_asset_id,
                        f"Inspeccion vencida: {inspection.inspection_name}",
                        AirworthinessBlockSeverity.GROUNDING,
                        actor_id,
                    )
                )

        for record in statistical_records:
            if record.status in {StatisticalControlStatus.OVERDUE, StatisticalControlStatus.GROUNDING_REQUIRED}:
                blocks.append(
                    self._block(
                        aircraft_asset_id,
                        f"Asset {record.asset_id} vencido o requiere bloqueo operacional.",
                        AirworthinessBlockSeverity.GROUNDING,
                        actor_id,
                    )
                )

        for counter in maintenance_counters:
            if counter.remaining_usage <= 0:
                blocks.append(
                    self._block(
                        aircraft_asset_id,
                        f"Maintenance overdue en asset {counter.asset_id}.",
                        AirworthinessBlockSeverity.CRITICAL,
                        actor_id,
                    )
                )

        return blocks

    def receive_component_from_arsenal(
        self,
        asset_id: UUID,
        origin_department_id: UUID,
        destination_department_id: UUID,
        performed_by: str,
        movement_date: datetime,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        return self._inventory_movement(
            asset_id,
            SquadronInventoryMovementType.RECEIVED_FROM_ARSENAL,
            origin_department_id,
            destination_department_id,
            performed_by,
            movement_date,
            notes,
            actor_id,
            "recibio componente desde Arsenal",
        )

    def deliver_component_for_installation(
        self,
        asset_id: UUID,
        origin_department_id: UUID,
        destination_department_id: UUID,
        performed_by: str,
        movement_date: datetime,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        return self._inventory_movement(
            asset_id,
            SquadronInventoryMovementType.DELIVERED_FOR_INSTALLATION,
            origin_department_id,
            destination_department_id,
            performed_by,
            movement_date,
            notes,
            actor_id,
            "entrego componente para montaje",
        )

    def prepare_component_for_arsenal_transfer(
        self,
        asset_id: UUID,
        origin_department_id: UUID,
        destination_department_id: UUID,
        performed_by: str,
        movement_date: datetime,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        return self._inventory_movement(
            asset_id,
            SquadronInventoryMovementType.PREPARED_FOR_ARSENAL_TRANSFER,
            origin_department_id,
            destination_department_id,
            performed_by,
            movement_date,
            notes,
            actor_id,
            "preparo componente para envio a Arsenal",
        )

    def _inventory_movement(
        self,
        asset_id: UUID,
        movement_type: SquadronInventoryMovementType,
        origin_department_id: UUID | None,
        destination_department_id: UUID | None,
        performed_by: str,
        movement_date: datetime,
        notes: str | None,
        actor_id: str,
        action: str,
    ) -> AuditedResult:
        movement = SquadronInventoryMovement(
            id=uuid4(),
            asset_id=asset_id,
            movement_type=movement_type,
            origin_department_id=origin_department_id,
            destination_department_id=destination_department_id,
            performed_by=performed_by,
            movement_date=movement_date,
            notes=notes,
        )
        return self._result(movement, actor_id, action, None, self._inventory_movement_state(movement))

    def _block(
        self,
        aircraft_asset_id: UUID,
        reason: str,
        severity: AirworthinessBlockSeverity,
        actor_id: str,
    ) -> AuditedResult:
        block = AirworthinessBlock(
            id=uuid4(),
            aircraft_asset_id=aircraft_asset_id,
            reason=reason,
            blocked_since=datetime.now(timezone.utc),
            severity=severity,
            active=True,
        )
        return self._result(block, actor_id, "registro bloqueo de aeronavegabilidad", None, self._block_state(block))

    def _result(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditedResult:
        return AuditedResult(
            entity=entity,
            audit_event=AuditEvent(
                id=uuid4(),
                actor_id=actor_id,
                action=action,
                entity_type=type(entity).__name__,
                entity_id=entity.id,
                timestamp=datetime.now(timezone.utc),
                before_state=before_state,
                after_state=after_state,
            ),
        )

    def _append_note(self, current_notes: str | None, note: str) -> str:
        if not current_notes:
            return note
        return f"{current_notes}\n{note}"

    def _mounted_component_state(self, mounted_component: MountedComponent) -> dict:
        return {
            "id": str(mounted_component.id),
            "aircraft_configuration_id": str(mounted_component.aircraft_configuration_id),
            "asset_id": str(mounted_component.asset_id),
            "position_code": mounted_component.position_code,
            "status": mounted_component.status,
        }

    def _maintenance_action_state(self, action: MaintenanceAction) -> dict:
        return {
            "id": str(action.id),
            "aircraft_asset_id": str(action.aircraft_asset_id),
            "action_type": action.action_type,
            "requires_quality_approval": action.requires_quality_approval,
            "status": action.status,
        }

    def _quality_approval_state(self, approval: SquadronQualityApproval) -> dict:
        return {
            "id": str(approval.id),
            "maintenance_action_id": str(approval.maintenance_action_id),
            "approved": approval.approved,
            "status": approval.status,
        }

    def _statistical_record_state(self, record: StatisticalControlRecord) -> dict:
        return {
            "id": str(record.id),
            "asset_id": str(record.asset_id),
            "current_hours": str(record.current_hours),
            "remaining_hours": str(record.remaining_hours) if record.remaining_hours is not None else None,
            "current_cycles": record.current_cycles,
            "remaining_cycles": record.remaining_cycles,
            "status": record.status,
        }

    def _inventory_movement_state(self, movement: SquadronInventoryMovement) -> dict:
        return {
            "id": str(movement.id),
            "asset_id": str(movement.asset_id),
            "movement_type": movement.movement_type,
            "origin_department_id": str(movement.origin_department_id) if movement.origin_department_id else None,
            "destination_department_id": str(movement.destination_department_id) if movement.destination_department_id else None,
        }

    def _block_state(self, block: AirworthinessBlock) -> dict:
        return {
            "id": str(block.id),
            "aircraft_asset_id": str(block.aircraft_asset_id),
            "reason": block.reason,
            "severity": block.severity,
            "active": block.active,
        }
