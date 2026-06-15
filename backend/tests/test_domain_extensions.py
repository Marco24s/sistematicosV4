from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.shared.domain.exceptions import DomainError

# Importar todos los modelos de la app para que SQLite los cree durante los tests
import app.modules.organization.domain.models
import app.modules.assets.domain.models
import app.modules.maintenance.domain.models
import app.modules.flight_operations.domain.models
import app.modules.arsenal_workflow.domain.models
import app.modules.squadron_operations.domain.models
import app.modules.personnel_certification.domain.models
import app.modules.document_management.domain.models
import app.modules.supply_chain.domain.models
import app.modules.tool_calibration.domain.models
import app.modules.authorization.domain.models
import app.modules.engine_management.domain.models
import app.modules.reporting_analytics.domain.models
import app.shared.infrastructure.event_store

# Modelos específicos del test
from app.modules.supply_chain.domain.models import StockItem, StockCondition
from app.modules.engine_management.domain.models import EngineAssembly, EngineCycleCounter, OilAnalysisRecord
from app.modules.squadron_operations.domain.models import AircraftConfigurationSnapshot
from app.modules.reporting_analytics.domain.models import FleetAvailabilityReport


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    yield session
    session.close()


def test_multi_unit_isolation(db_session: Session) -> None:
    # 1. Crear items con aislamiento
    unit_helicopter = uuid4()
    unit_antisubmarine = uuid4()
    
    item_helicopter = StockItem(
        id=uuid4(),
        asset_id=uuid4(),
        location_id=uuid4(),
        quantity=1,
        available_quantity=1,
        condition=StockCondition.SERVICEABLE,
        last_updated=datetime.now(timezone.utc),
        military_unit_id=unit_helicopter
    )
    item_antisubmarine = StockItem(
        id=uuid4(),
        asset_id=uuid4(),
        location_id=uuid4(),
        quantity=1,
        available_quantity=1,
        condition=StockCondition.SERVICEABLE,
        last_updated=datetime.now(timezone.utc),
        military_unit_id=unit_antisubmarine
    )
    db_session.add_all([item_helicopter, item_antisubmarine])
    db_session.commit()

    # Verificar aislamiento
    assert item_helicopter.military_unit_id == unit_helicopter
    assert item_antisubmarine.military_unit_id == unit_antisubmarine
    assert item_helicopter.military_unit_id != item_antisubmarine.military_unit_id


def test_serialized_inventory(db_session: Session) -> None:
    asset_id = uuid4()
    item_serial_01 = StockItem(
        id=uuid4(),
        asset_id=asset_id,
        location_id=uuid4(),
        quantity=1,
        available_quantity=1,
        condition=StockCondition.SERVICEABLE,
        last_updated=datetime.now(timezone.utc),
        serial_number="SN-ENG-01",
        serialized_inventory=True
    )
    db_session.add(item_serial_01)
    db_session.commit()

    assert item_serial_01.serial_number == "SN-ENG-01"
    assert item_serial_01.serialized_inventory is True


def test_engine_management_cycle_counting(db_session: Session) -> None:
    engine_id = uuid4()
    assembly = EngineAssembly(
        id=uuid4(),
        asset_id=engine_id,
        engine_model="PT6A-67D",
        serial_number="ENG-PT6-7711"
    )
    db_session.add(assembly)
    db_session.commit()

    counters = EngineCycleCounter(
        engine_assembly_id=assembly.id,
        total_operating_hours=Decimal("150.50"),
        total_start_cycles=120,
        total_ng_cycles=1400,
        total_np_cycles=1200
    )
    db_session.add(counters)
    
    oil_record = OilAnalysisRecord(
        engine_assembly_id=assembly.id,
        sampled_at=datetime.now(timezone.utc).date(),
        iron_ppm=4.2,
        copper_ppm=1.1,
        silicon_ppm=0.5,
        verdict="NORMAL"
    )
    db_session.add(oil_record)
    db_session.commit()

    assert counters.total_start_cycles == 120
    assert oil_record.verdict == "NORMAL"


def test_historical_configuration_snapshot(db_session: Session) -> None:
    aircraft_id = uuid4()
    snapshot = AircraftConfigurationSnapshot(
        aircraft_id=aircraft_id,
        snapshot_date=datetime.now(timezone.utc),
        flight_hours=Decimal("2340.50"),
        installed_components_json={"engine_left": "SN-PT6-01", "radar": "SN-RADAR-02"},
        created_by="STATISTICS_OFFICER"
    )
    db_session.add(snapshot)
    db_session.commit()

    assert snapshot.aircraft_id == aircraft_id
    assert snapshot.installed_components_json["engine_left"] == "SN-PT6-01"


def test_reporting_analytics_availability(db_session: Session) -> None:
    report = FleetAvailabilityReport(
        report_date=datetime.now(timezone.utc).date(),
        total_aircraft=12,
        available_aircraft=8,
        non_operational_aircraft=4
    )
    db_session.add(report)
    db_session.commit()

    assert report.total_aircraft == 12
    assert report.available_aircraft == 8
