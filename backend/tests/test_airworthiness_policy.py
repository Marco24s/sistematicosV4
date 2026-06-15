from datetime import date, timedelta
from uuid import uuid4

from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, TechnicalHistory
from app.modules.assets.domain.services import AirworthinessPolicy
from app.modules.maintenance.domain.models import MaintenanceCounter


def make_asset() -> Asset:
    return Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="PN-001",
        serial_number="SN-001",
        nomenclature="Hydraulic Pump",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
    )


def test_airworthiness_blocks_asset_without_technical_history() -> None:
    asset = make_asset()

    assessment = AirworthinessPolicy().assess(asset)

    assert assessment.is_airworthy is False
    assert assessment.findings[0].code == "missing_technical_history"


def test_airworthiness_blocks_expired_calendar_life() -> None:
    asset = make_asset()
    asset.technical_history = TechnicalHistory(
        id=uuid4(),
        asset_id=asset.id,
        opened_date=date.today() - timedelta(days=365),
        current_total_hours=100,
        current_total_cycles=20,
        calendar_expiration=date.today() - timedelta(days=1),
    )

    assessment = AirworthinessPolicy().assess(asset)

    assert assessment.is_airworthy is False
    assert assessment.findings[0].code == "calendar_expired"


def test_airworthiness_blocks_due_maintenance_counter() -> None:
    asset = make_asset()
    asset.technical_history = TechnicalHistory(
        id=uuid4(),
        asset_id=asset.id,
        opened_date=date.today(),
        current_total_hours=0,
        current_total_cycles=0,
    )
    counter = MaintenanceCounter(
        id=uuid4(),
        asset_id=asset.id,
        maintenance_program_id=uuid4(),
        current_usage=100,
        remaining_usage=0,
    )

    assessment = AirworthinessPolicy().assess(asset, [counter])

    assert assessment.is_airworthy is False
    assert assessment.findings[0].code == "maintenance_due"
