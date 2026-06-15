from uuid import UUID
from sqlalchemy.orm import Session

from app.shared.domain.commands import Command
from app.shared.domain.events import DomainEvent
from app.shared.events.bus import command_bus

# Imports de Comandos de Negocio
from app.modules.workflow_orchestration.domain.commands import (
    CreateMaintenanceRequestCommand,
    CreateQualityInspectionCommand,
    CreateServiceReleaseCommand,
    UpdateTechnicalHistoryCommand,
    UpdateServiceStatusCommand,
    CreateStockAvailabilityCommand,
    BlockAircraftCommand
)

# Imports de Application Services Fachadas
from app.modules.document_management.application.services import DocumentManagementApplicationService
from app.modules.supply_chain.application.services import SupplyChainApplicationService
from app.modules.arsenal_workflow.application.services import ArsenalWorkflowApplicationService
from app.modules.squadron_operations.application.services import SquadronOperationsApplicationService
from app.modules.assets.application.services import AssetsApplicationService

# Instanciamos los servicios
doc_service = DocumentManagementApplicationService()
supply_service = SupplyChainApplicationService()
arsenal_service = ArsenalWorkflowApplicationService()
squadron_service = SquadronOperationsApplicationService()
assets_service = AssetsApplicationService()


# ==========================================
# COMMAND HANDLERS
# ==========================================

def handle_create_maintenance_request(command: Command, session: Session) -> None:
    asset_id = UUID(command.payload["asset_id"])
    priority = command.payload.get("priority", "NORMAL")
    fr_id_str = command.payload.get("failure_report_id")
    fr_id = UUID(fr_id_str) if fr_id_str else None
    arsenal_service.create_maintenance_request(asset_id, priority, session, failure_report_id=fr_id)


def handle_create_quality_inspection(command: Command, session: Session) -> None:
    repair_task_id = UUID(command.payload["repair_task_id"])
    arsenal_service.create_quality_inspection(repair_task_id, session)


def handle_create_service_release(command: Command, session: Session) -> None:
    asset_id = UUID(command.payload["asset_id"])
    inspection_id = UUID(command.payload["inspection_id"])
    arsenal_service.create_service_release(asset_id, inspection_id, session)


def handle_update_technical_history(command: Command, session: Session) -> None:
    asset_id = UUID(command.payload["asset_id"])
    action_type = command.payload["action_type"]
    notes = command.payload.get("notes", "")
    hours = float(command.payload.get("hours", 0.0))
    cycles = int(command.payload.get("cycles", 0))
    doc_service.create_technical_history_entry(asset_id, action_type, notes, hours, cycles, session)


def handle_update_service_status(command: Command, session: Session) -> None:
    asset_id = UUID(command.payload["asset_id"])
    status = command.payload["status"]
    doc_service.update_service_status(asset_id, status, session)


def handle_create_stock_availability(command: Command, session: Session) -> None:
    asset_id = UUID(command.payload["asset_id"])
    location_id = UUID(command.payload["location_id"])
    supply_service.create_stock_item_serviceable(asset_id, location_id, session)


def handle_block_aircraft(command: Command, session: Session) -> None:
    aircraft_id = UUID(command.payload["aircraft_id"])
    reason = command.payload["reason"]
    squadron_service.block_aircraft(aircraft_id, reason, session)


# ==========================================
# EVENT HANDLERS
# ==========================================

def handle_flight_closed(event: DomainEvent, session: Session) -> None:
    # Despacha comando para actualizar historial técnico
    payload = event.payload
    cmd = UpdateTechnicalHistoryCommand(
        payload={
            "asset_id": payload["aircraft_id"],
            "action_type": "FLIGHT_CLOSED",
            "notes": f"Flight closed. Hours: {payload['flight_hours']}",
            "hours": payload["flight_hours"],
            "cycles": 1
        }
    )
    command_bus.dispatch(cmd, session)


def handle_failure_detected(event: DomainEvent, session: Session) -> None:
    payload = event.payload
    
    # 1. Crear solicitud de mantenimiento
    cmd_req = CreateMaintenanceRequestCommand(
        payload={
            "asset_id": payload["asset_id"],
            "priority": "CRITICAL",
            "failure_report_id": payload.get("failure_report_id")
        }
    )

    command_bus.dispatch(cmd_req, session)
    
    # 2. Bloquear la aeronave afectada
    cmd_block = BlockAircraftCommand(
        payload={
            "aircraft_id": payload["aircraft_id"],
            "reason": f"Failure report: {payload['failure_report_id']}"
        }
    )
    command_bus.dispatch(cmd_block, session)


def handle_repair_task_completed(event: DomainEvent, session: Session) -> None:
    payload = event.payload
    
    # 1. Crear inspección de calidad
    cmd_inspection = CreateQualityInspectionCommand(
        payload={
            "repair_task_id": payload["repair_task_id"]
        }
    )
    command_bus.dispatch(cmd_inspection, session)
    
    # 2. Actualizar estado a INSPECTION_REQUIRED
    cmd_status = UpdateServiceStatusCommand(
        payload={
            "asset_id": payload["asset_id"],
            "status": "INSPECTION_REQUIRED"
        }
    )
    command_bus.dispatch(cmd_status, session)


def handle_quality_inspection_approved(event: DomainEvent, session: Session) -> None:
    payload = event.payload
    cmd = CreateServiceReleaseCommand(
        payload={
            "asset_id": payload["asset_id"],
            "inspection_id": payload["inspection_id"]
        }
    )
    command_bus.dispatch(cmd, session)


def handle_service_released(event: DomainEvent, session: Session) -> None:
    payload = event.payload
    
    # 1. Registrar stock serviceable
    cmd_stock = CreateStockAvailabilityCommand(
        payload={
            "asset_id": payload["asset_id"],
            "location_id": payload["release_id"]
        }
    )
    command_bus.dispatch(cmd_stock, session)
    
    # 2. Actualizar estado de servicio a SERVICEABLE
    cmd_status = UpdateServiceStatusCommand(
        payload={
            "asset_id": payload["asset_id"],
            "status": "SERVICEABLE"
        }
    )
    command_bus.dispatch(cmd_status, session)


def handle_purchase_approved(event: DomainEvent, session: Session) -> None:
    payload = event.payload
    
    # Crear stock item disponible en bodega de compras
    cmd_stock = CreateStockAvailabilityCommand(
        payload={
            "asset_id": payload["asset_id"],
            "location_id": payload["purchase_order_id"]
        }
    )
    command_bus.dispatch(cmd_stock, session)


def handle_certification_expired(event: DomainEvent, session: Session) -> None:
    # Bloquear tareas del técnico mediante la fachada
    squadron_service.block_technician_tasks(UUID(event.payload["technician_id"]), session)
