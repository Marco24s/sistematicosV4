from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.shared.domain.exceptions import DomainError
from app.shared.events.bus import event_bus, command_bus

# Importamos todos los modelos ORM de la app para que SQLite los cree durante los tests
import app.modules.organization.domain.models
import app.modules.assets.domain.models
import app.modules.maintenance.domain.models
import app.modules.flight_operations.domain.models
import app.modules.arsenal_workflow.domain.models
import app.modules.squadron_operations.domain.models
import app.modules.personnel_certification.domain.models
import app.modules.document_management.domain.models
import app.modules.supply_chain.domain.models
import app.shared.infrastructure.event_store

# Modelos y agregados
from app.modules.workflow_orchestration.domain.models import WorkflowInstance, WorkflowStatus, RepairCycleState

from app.modules.workflow_orchestration.orchestrator import RepairCycleOrchestrator
from app.modules.workflow_orchestration.domain.events import (
    FlightClosedEvent,
    FailureDetectedEvent,
    RepairTaskCompletedEvent,
    QualityInspectionApprovedEvent,
    ServiceReleasedEvent,
    PurchaseApprovedEvent,
    CertificationExpiredEvent
)
from app.modules.workflow_orchestration.domain.commands import (
    CreateMaintenanceRequestCommand,
    CreateQualityInspectionCommand,
    CreateServiceReleaseCommand,
    UpdateTechnicalHistoryCommand,
    UpdateServiceStatusCommand,
    CreateStockAvailabilityCommand,
    BlockAircraftCommand
)

# Inicializamos BD SQLite en memoria para tests de integración
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    yield session
    session.close()


def test_domain_event_fields() -> None:
    event_id = uuid4()
    aggregate_id = uuid4()
    event = FlightClosedEvent(
        event_id=event_id,
        aggregate_id=aggregate_id,
        payload={"aircraft_id": str(aggregate_id), "flight_hours": 2.5}
    )
    assert event.event_id == event_id
    assert event.aggregate_id == aggregate_id
    assert event.event_type == "FlightClosedEvent"
    assert event.aggregate_type == "flight_operations"
    assert event.payload["flight_hours"] == 2.5


def test_event_bus_subscribe_and_publish(db_session: Session) -> None:
    # Limpiar eventos previos de tests anteriores
    event_bus.published_events.clear()
    
    aircraft_id = uuid4()
    event = FlightClosedEvent(
        aggregate_id=aircraft_id,
        payload={"aircraft_id": str(aircraft_id), "flight_hours": 3.0}
    )
    
    event_bus.publish(event, db_session)
    db_session.commit()

    assert len(event_bus.published_events) == 1
    assert event_bus.published_events[0].aggregate_id == aircraft_id


def test_command_bus_idempotency(db_session: Session) -> None:
    command_bus.dispatched_commands.clear()
    
    cmd_id = uuid4()
    asset_id = uuid4()
    
    cmd = CreateMaintenanceRequestCommand(
        command_id=cmd_id,
        payload={"asset_id": str(asset_id), "priority": "HIGH"}
    )
    
    # Primera ejecución
    command_bus.dispatch(cmd, db_session)
    db_session.commit()
    
    # Segunda ejecución del mismo comando (mismo command_id)
    command_bus.dispatch(cmd, db_session)
    db_session.commit()
    
    # Debe haberse ruteado y guardado, pero saltarse la segunda ejecución real gracias a la idempotencia
    # La lista in-memory registra el intento de dispatch, pero la base de datos registra procesado = True
    from app.shared.infrastructure.event_store import StoredCommand
    from sqlalchemy import select
    
    stmt = select(StoredCommand).where(StoredCommand.command_id == cmd_id)
    stored = db_session.scalars(stmt).first()
    assert stored is not None
    assert stored.processed is True
    assert stored.retry_count == 0


def test_orchestrator_valid_transition(db_session: Session) -> None:
    orchestrator = RepairCycleOrchestrator()
    correlation_id = uuid4()
    
    # Iniciar workflow
    instance = orchestrator.start(correlation_id, db_session)
    db_session.commit()
    
    assert instance.current_state == RepairCycleState.FAILURE_DETECTED
    assert instance.status == WorkflowStatus.RUNNING
    
    # Transición válida a REQUEST_CREATED
    orchestrator.transition(instance, RepairCycleState.REQUEST_CREATED, db_session)
    db_session.commit()
    
    assert instance.current_state == RepairCycleState.REQUEST_CREATED
    assert len(instance.transition_logs) == 2


def test_orchestrator_invalid_transition_raises(db_session: Session) -> None:
    orchestrator = RepairCycleOrchestrator()
    correlation_id = uuid4()
    
    instance = orchestrator.start(correlation_id, db_session)
    db_session.commit()
    
    # Transicionar directamente a STOCK_AVAILABLE sin pasar por pasos intermedios (Inválido)
    with pytest.raises(DomainError):
        orchestrator.transition(instance, RepairCycleState.STOCK_AVAILABLE, db_session)


def test_complete_and_fail_workflow(db_session: Session) -> None:
    orchestrator = RepairCycleOrchestrator()
    correlation_id = uuid4()
    
    instance = orchestrator.start(correlation_id, db_session)
    db_session.commit()
    
    orchestrator.complete(instance, db_session)
    db_session.commit()
    assert instance.status == WorkflowStatus.COMPLETED
    assert instance.completed_at is not None
    
    # Fail workflow
    correlation_id_2 = uuid4()
    instance_2 = orchestrator.start(correlation_id_2, db_session)
    db_session.commit()
    
    orchestrator.fail(instance_2, db_session, "Component condemned by quality inspection")
    db_session.commit()
    assert instance_2.status == WorkflowStatus.FAILED


def test_event_handler_dispatches_commands(db_session: Session) -> None:
    command_bus.dispatched_commands.clear()
    
    aircraft_id = uuid4()
    event = FailureDetectedEvent(
        aggregate_id=aircraft_id,
        payload={"aircraft_id": str(aircraft_id), "asset_id": str(aircraft_id), "failure_report_id": str(uuid4())}
    )
    
    event_bus.publish(event, db_session)
    db_session.commit()
    
    # Debería haber despachado CreateMaintenanceRequestCommand y BlockAircraftCommand
    dispatched_types = [c.command_type for c in command_bus.dispatched_commands]
    assert "CreateMaintenanceRequestCommand" in dispatched_types
    assert "BlockAircraftCommand" in dispatched_types
