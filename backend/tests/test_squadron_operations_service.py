from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, TechnicalHistory
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.modules.squadron_operations.domain.models import (
    AircraftConfiguration,
    AircraftInspectionIntervalType,
    AircraftInspectionProgram,
    AircraftInspectionStatus,
    AirworthinessBlockSeverity,
    MaintenanceActionStatus,
    MountedComponent,
    MountedComponentStatus,
    SquadronInventoryMovementType,
    SquadronQualityApprovalStatus,
    StatisticalControlRecord,
    StatisticalControlStatus,
)
from app.modules.squadron_operations.domain.services import SquadronOperationsService
from app.shared.domain.exceptions import DomainError


def make_asset(serial_number: str = "ASSET-001") -> Asset:
    return Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="PN-001",
        serial_number=serial_number,
        nomenclature="Aircraft or component",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
    )


def make_history(asset: Asset) -> TechnicalHistory:
    return TechnicalHistory(
        id=uuid4(),
        asset_id=asset.id,
        opened_date=date.today(),
        current_total_hours=120,
        current_total_cycles=42,
    )


def test_install_and_remove_component_updates_history_and_audit() -> None:
    service = SquadronOperationsService()
    aircraft = make_asset("AIR-001")
    component = make_asset("COMP-001")
    history = make_history(component)
    configuration = AircraftConfiguration(
        id=uuid4(),
        aircraft_asset_id=aircraft.id,
        configuration_name="Operational configuration",
        active=True,
    )

    install_result = service.install_component_on_aircraft(
        aircraft_configuration=configuration,
        component_asset=component,
        component_history=history,
        position_code="HYDRAULIC_SYSTEM",
        installation_date=datetime.now(timezone.utc),
        installed_by="maintenance-tech",
        actor_id="maintenance-tech",
    )
    mounted = install_result.entity

    assert mounted.status == MountedComponentStatus.ACTIVE
    assert "Installed on aircraft" in history.notes
    assert install_result.audit_event.entity_type == "MountedComponent"

    remove_result = service.remove_component_from_aircraft(
        mounted_component=mounted,
        component_history=history,
        removed_by="maintenance-tech",
        removed_at=datetime.now(timezone.utc),
        actor_id="maintenance-tech",
    )

    assert mounted.status == MountedComponentStatus.REMOVED
    assert "Removed by" in history.notes
    assert remove_result.audit_event.before_state["status"] == MountedComponentStatus.ACTIVE


def test_remove_component_rejects_non_active_mount() -> None:
    component = make_asset("COMP-002")
    mounted = MountedComponent(
        id=uuid4(),
        aircraft_configuration_id=uuid4(),
        asset_id=component.id,
        position_code="NOSE_WHEEL",
        installation_date=datetime.now(timezone.utc),
        installed_by="maintenance-tech",
        status=MountedComponentStatus.REMOVED,
    )

    with pytest.raises(DomainError):
        SquadronOperationsService().remove_component_from_aircraft(
            mounted_component=mounted,
            component_history=make_history(component),
            removed_by="maintenance-tech",
            removed_at=datetime.now(timezone.utc),
            actor_id="maintenance-tech",
        )


def test_register_and_approve_maintenance_action() -> None:
    service = SquadronOperationsService()
    action_result = service.register_maintenance_action(
        aircraft_asset_id=uuid4(),
        performed_by="maintenance-tech",
        action_type="PRE_FLIGHT_INSPECTION",
        description="Inspeccion previa vuelo completa.",
        performed_at=datetime.now(timezone.utc),
        requires_quality_approval=True,
        actor_id="maintenance-tech",
    )
    action = action_result.entity

    assert action.status == MaintenanceActionStatus.WAITING_QUALITY

    approval_result = service.approve_maintenance_action(
        maintenance_action=action,
        inspector_id=uuid4(),
        approved=True,
        notes="Tarea verificada y conforme.",
        approved_at=datetime.now(timezone.utc),
        actor_id="quality-inspector",
    )

    assert action.status == MaintenanceActionStatus.COMPLETED
    assert approval_result.entity.status == SquadronQualityApprovalStatus.APPROVED
    assert approval_result.audit_event.action == "aprobo tarea de mantenimiento escuadrilla"


def test_update_statistical_control_recalculates_remaining_hours() -> None:
    asset = make_asset("AIR-003")
    history = make_history(asset)
    record = StatisticalControlRecord(
        id=uuid4(),
        asset_id=asset.id,
        current_hours=Decimal("0"),
        remaining_hours=None,
        current_cycles=0,
        remaining_cycles=None,
        status=StatisticalControlStatus.NORMAL,
    )
    counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=asset.id,
        maintenance_program_id=uuid4(),
        current_usage=20,
        remaining_usage=4,
    )

    result = SquadronOperationsService().update_statistical_control(
        record=record,
        technical_history=history,
        maintenance_counters=[counter],
        warning_threshold=5,
        actor_id="statistics",
    )

    assert record.current_hours == Decimal("120")
    assert record.remaining_hours == Decimal("4")
    assert record.status == StatisticalControlStatus.WARNING
    assert result.audit_event.entity_type == "StatisticalControlRecord"


def test_evaluate_operational_readiness_creates_blocks() -> None:
    aircraft_id = uuid4()
    inspection = AircraftInspectionProgram(
        id=uuid4(),
        aircraft_asset_id=aircraft_id,
        inspection_name="100 Hour Inspection",
        interval_type=AircraftInspectionIntervalType.FLIGHT_HOURS,
        interval_value=100,
        next_due=date.today() - timedelta(days=1),
        status=AircraftInspectionStatus.ACTIVE,
    )
    record = StatisticalControlRecord(
        id=uuid4(),
        asset_id=uuid4(),
        current_hours=Decimal("100"),
        remaining_hours=Decimal("0"),
        current_cycles=10,
        remaining_cycles=0,
        status=StatisticalControlStatus.OVERDUE,
    )
    counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=record.asset_id,
        maintenance_program_id=uuid4(),
        current_usage=100,
        remaining_usage=0,
    )

    blocks = SquadronOperationsService().evaluate_operational_readiness(
        aircraft_asset_id=aircraft_id,
        inspection_programs=[inspection],
        statistical_records=[record],
        maintenance_counters=[counter],
        actor_id="statistics",
    )

    assert len(blocks) == 3
    assert all(block.entity.active for block in blocks)
    assert {block.entity.severity for block in blocks} == {
        AirworthinessBlockSeverity.GROUNDING,
        AirworthinessBlockSeverity.CRITICAL,
    }


def test_inventory_movements_are_audited() -> None:
    service = SquadronOperationsService()
    asset_id = uuid4()
    arsenal_id = uuid4()
    store_id = uuid4()
    maintenance_id = uuid4()

    received = service.receive_component_from_arsenal(
        asset_id=asset_id,
        origin_department_id=arsenal_id,
        destination_department_id=store_id,
        performed_by="pañol",
        movement_date=datetime.now(timezone.utc),
        notes="Recibido con certificado de calidad.",
        actor_id="store-operator",
    )
    delivered = service.deliver_component_for_installation(
        asset_id=asset_id,
        origin_department_id=store_id,
        destination_department_id=maintenance_id,
        performed_by="pañol",
        movement_date=datetime.now(timezone.utc),
        notes="Entregado para montaje.",
        actor_id="store-operator",
    )
    prepared = service.prepare_component_for_arsenal_transfer(
        asset_id=asset_id,
        origin_department_id=store_id,
        destination_department_id=arsenal_id,
        performed_by="pañol",
        movement_date=datetime.now(timezone.utc),
        notes="Preparado con parte de falla e historial.",
        actor_id="store-operator",
    )

    assert received.entity.movement_type == SquadronInventoryMovementType.RECEIVED_FROM_ARSENAL
    assert delivered.entity.movement_type == SquadronInventoryMovementType.DELIVERED_FOR_INSTALLATION
    assert prepared.entity.movement_type == SquadronInventoryMovementType.PREPARED_FOR_ARSENAL_TRANSFER
    assert all(result.audit_event.entity_type == "SquadronInventoryMovement" for result in [received, delivered, prepared])
