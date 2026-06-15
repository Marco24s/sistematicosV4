from app.shared.events.bus import event_bus, command_bus

# Imports de handlers
from app.modules.workflow_orchestration.application.handlers import (
    handle_flight_closed,
    handle_failure_detected,
    handle_repair_task_completed,
    handle_quality_inspection_approved,
    handle_service_released,
    handle_purchase_approved,
    handle_certification_expired,
    # Command handlers
    handle_create_maintenance_request,
    handle_create_quality_inspection,
    handle_create_service_release,
    handle_update_technical_history,
    handle_update_service_status,
    handle_create_stock_availability,
    handle_block_aircraft
)

def register_workflow_orchestration(event_bus_instance, command_bus_instance) -> None:
    # Registrar Event Handlers
    event_bus_instance.subscribe("FlightClosedEvent", handle_flight_closed)
    event_bus_instance.subscribe("FailureDetectedEvent", handle_failure_detected)
    event_bus_instance.subscribe("RepairTaskCompletedEvent", handle_repair_task_completed)
    event_bus_instance.subscribe("QualityInspectionApprovedEvent", handle_quality_inspection_approved)
    event_bus_instance.subscribe("ServiceReleasedEvent", handle_service_released)
    event_bus_instance.subscribe("PurchaseApprovedEvent", handle_purchase_approved)
    event_bus_instance.subscribe("CertificationExpiredEvent", handle_certification_expired)

    # Registrar Command Handlers
    command_bus_instance.register("CreateMaintenanceRequestCommand", handle_create_maintenance_request)
    command_bus_instance.register("CreateQualityInspectionCommand", handle_create_quality_inspection)
    command_bus_instance.register("CreateServiceReleaseCommand", handle_create_service_release)
    command_bus_instance.register("UpdateTechnicalHistoryCommand", handle_update_technical_history)
    command_bus_instance.register("UpdateServiceStatusCommand", handle_update_service_status)
    command_bus_instance.register("CreateStockAvailabilityCommand", handle_create_stock_availability)
    command_bus_instance.register("BlockAircraftCommand", handle_block_aircraft)

# Registro automático en la importación para facilitar bootstrap
register_workflow_orchestration(event_bus, command_bus)
