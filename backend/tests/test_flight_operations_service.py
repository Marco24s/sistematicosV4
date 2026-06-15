from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, TechnicalHistory
from app.modules.flight_operations.domain.models import (
    FlightSheet,
    FlightSheetStatus,
    InstalledAsset,
    InstalledAssetStatus,
    Mission,
    MissionStatus,
    MissionType,
    OperationalAlertSeverity,
)
from app.modules.flight_operations.domain.services import FlightClosureInput, FlightOperationsService
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.shared.domain.exceptions import DomainError


def make_asset(asset_id=None, serial_number="SN-001") -> Asset:
    return Asset(
        id=asset_id or uuid4(),
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
        opened_date=datetime.now(timezone.utc).date(),
        current_total_hours=100,
        current_total_cycles=10,
    )


def make_mission() -> Mission:
    return Mission(
        id=uuid4(),
        organization_id=uuid4(),
        mission_code="TRN-001",
        mission_type=MissionType.TRAINING,
        planned_flight_hours=Decimal("2.00"),
        status=MissionStatus.IN_PROGRESS,
    )


def make_flight_sheet(mission: Mission, aircraft: Asset) -> FlightSheet:
    return FlightSheet(
        id=uuid4(),
        mission_id=mission.id,
        aircraft_asset_id=aircraft.id,
        fuel_loaded=Decimal("1200.00"),
        aircraft_weight=Decimal("8400.00"),
        planned_departure_time=datetime.now(timezone.utc),
        actual_departure_time=datetime.now(timezone.utc),
        actual_arrival_time=datetime.now(timezone.utc) + timedelta(hours=2),
        planned_hours=Decimal("2.00"),
        actual_hours_flown=Decimal("2.00"),
        status=FlightSheetStatus.LANDED,
    )


def test_close_flight_consumes_aircraft_and_installed_asset_life() -> None:
    aircraft = make_asset(serial_number="AIR-001")
    component = make_asset(serial_number="COMP-001")
    mission = make_mission()
    flight_sheet = make_flight_sheet(mission, aircraft)
    aircraft_history = make_history(aircraft)
    component_history = make_history(component)
    installed_asset = InstalledAsset(
        id=uuid4(),
        aircraft_asset_id=aircraft.id,
        installed_asset_id=component.id,
        position_code="HYDRAULIC_SYSTEM",
        installation_date=datetime.now(timezone.utc),
        installed_by="TECH-001",
        status=InstalledAssetStatus.INSTALLED,
    )
    aircraft_counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=aircraft.id,
        maintenance_program_id=uuid4(),
        current_usage=23,
        remaining_usage=2,
    )
    component_counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=component.id,
        maintenance_program_id=uuid4(),
        current_usage=98,
        remaining_usage=2,
    )

    result = FlightOperationsService().close_flight(
        FlightClosureInput(
            mission=mission,
            flight_sheet=flight_sheet,
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_assets=[installed_asset],
            installed_asset_histories={component.id: component_history},
            maintenance_counters_by_asset_id={
                aircraft.id: [aircraft_counter],
                component.id: [component_counter],
            },
            remaining_usage_threshold=5,
            cycles_consumed=1,
        )
    )

    assert flight_sheet.status == FlightSheetStatus.CLOSED
    assert mission.status == MissionStatus.COMPLETED
    assert aircraft_history.current_total_hours == Decimal("102.00")
    assert component_history.current_total_hours == Decimal("102.00")
    assert aircraft_history.current_total_cycles == 11
    assert component_history.current_total_cycles == 11
    assert aircraft_counter.remaining_usage == 0
    assert component_counter.remaining_usage == 0
    assert len(result.consumption_events) == 2
    assert {event.asset_id for event in result.consumption_events} == {aircraft.id, component.id}
    assert len(result.alerts) == 2
    assert all(alert.severity == OperationalAlertSeverity.CRITICAL for alert in result.alerts)


def test_close_flight_requires_actual_hours() -> None:
    aircraft = make_asset()
    mission = make_mission()
    flight_sheet = make_flight_sheet(mission, aircraft)
    flight_sheet.actual_hours_flown = None

    with pytest.raises(DomainError):
        FlightOperationsService().close_flight(
            FlightClosureInput(
                mission=mission,
                flight_sheet=flight_sheet,
                aircraft=aircraft,
                aircraft_history=make_history(aircraft),
                installed_assets=[],
                installed_asset_histories={},
            )
        )


def test_detect_airworthiness_risk_finds_overdue_counter_and_expired_component() -> None:
    aircraft = make_asset(serial_number="AIR-001")
    component = make_asset(serial_number="COMP-001")
    aircraft_history = make_history(aircraft)
    component_history = make_history(component)
    component_history.calendar_expiration = datetime.now(timezone.utc).date() - timedelta(days=1)
    counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=aircraft.id,
        maintenance_program_id=uuid4(),
        current_usage=100,
        remaining_usage=0,
    )

    assessment = FlightOperationsService().detect_airworthiness_risk(
        aircraft=aircraft,
        aircraft_history=aircraft_history,
        installed_asset_histories=[component_history],
        maintenance_counters_by_asset_id={aircraft.id: [counter]},
    )

    assert assessment.is_airworthy is False
    assert {risk.code for risk in assessment.risks} == {"calendar_expired", "maintenance_overdue"}
