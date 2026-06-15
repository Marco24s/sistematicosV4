import pytest
import sqlite3
from datetime import date, datetime, timedelta
from uuid import uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Register Decimal adapter for SQLite
sqlite3.register_adapter(Decimal, lambda d: float(d))

# Import all models to populate SQLAlchemy metadata registry
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
import app.modules.workflow_orchestration.domain.models
import app.modules.reporting_analytics.domain.models
import app.modules.flight_release_control.domain.models
import app.modules.airworthiness_engine.domain.models
import app.modules.disposal_management.domain.models
import app.modules.asset_reallocation.domain.models
import app.modules.configuration_baseline.domain.models
import app.modules.structural_fatigue.domain.models
import app.modules.maintenance_human_factors.domain.models
import app.modules.reliability_engine.domain.models
import app.modules.fod_management.domain.models
import app.modules.tool_calibration.domain.models

from app.main import app
from app.core.database import Base, get_db
from app.modules.organization.domain.models import Organization, OrganizationType, Department, DepartmentType
from app.modules.assets.domain.models import Asset, AssetType, TechnicalHistory, AssetStatus, AssetCondition, AssetClassification
from app.modules.maintenance.domain.models import FailureReport, FailureSeverity
from app.modules.arsenal_workflow.domain.models import MaintenanceRequest

# Setup clean SQLite in-memory database for testing
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    yield session
    session.close()


@pytest.fixture(name="client")
def fixture_client(db_session):
    # Override FastAPI dependency to use test database session
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_register_asset_endpoint(client, db_session):
    org = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    asset_type = AssetType(id=uuid4(), name="Aeronave", category="AIRCRAFT")
    db_session.add_all([org, asset_type])
    db_session.commit()

    payload = {
        "serial_number": "SN-TEST-999",
        "asset_type_id": str(asset_type.id),
        "organization_id": str(org.id),
        "classification": "REPAIRABLE",
        "part_number": "PN-TEST",
        "nomenclature": "Test Seahawk"
    }

    response = client.post("/api/v1/assets/register", json=payload)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["serial_number"] == "SN-TEST-999"
    assert data["classification"] == "REPAIRABLE"
    assert data["status"] == "IN_STOCK"

    # Verify database state
    asset = db_session.query(Asset).filter_by(serial_number="SN-TEST-999").first()
    assert asset is not None
    assert asset.nomenclature == "Test Seahawk"


def test_get_asset_endpoint(client, db_session):
    org = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    asset_type = AssetType(id=uuid4(), name="Aeronave", category="AIRCRAFT")
    db_session.add_all([org, asset_type])
    db_session.commit()

    asset = Asset(
        id=uuid4(),
        asset_type_id=asset_type.id,
        part_number="PN-001",
        serial_number="SN-001",
        nomenclature="Hydraulic Pump",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=org.id
    )
    history = TechnicalHistory(
        id=uuid4(),
        asset_id=asset.id,
        opened_date=date.today(),
        current_total_hours=120,
        current_total_cycles=30
    )
    db_session.add_all([asset, history])
    db_session.commit()

    response = client.get(f"/api/v1/assets/{asset.id}")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["nomenclature"] == "Hydraulic Pump"
    assert data["technical_history"]["current_total_hours"] == 120.0
    assert data["technical_history"]["current_total_cycles"] == 30


def test_close_flight_endpoint(client, db_session):
    org = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    asset_type = AssetType(id=uuid4(), name="Aeronave", category="AIRCRAFT")
    aircraft = Asset(
        id=uuid4(),
        asset_type_id=asset_type.id,
        part_number="PN-AC",
        serial_number="SN-AC",
        nomenclature="Aircraft",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=org.id
    )
    db_session.add_all([org, asset_type, aircraft])
    db_session.commit()

    payload = {
        "aircraft_id": str(aircraft.id),
        "flight_hours": 3.5
    }

    # Login to get JWT
    login_res = client.post("/api/v1/auth/login", json={"username": "chief_maintenance", "password": "any"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/flight/close", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["status"] == "closed"
    assert data["aircraft"]["total_hours"] == 3.5
    assert data["aircraft"]["status"] == "RELEASED"


def test_report_failure_endpoint(client, db_session):
    org = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    asset_type = AssetType(id=uuid4(), name="Aeronave", category="AIRCRAFT")
    aircraft = Asset(
        id=uuid4(),
        asset_type_id=asset_type.id,
        part_number="PN-AC",
        serial_number="SN-AC",
        nomenclature="Aircraft",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=org.id
    )
    component = Asset(
        id=uuid4(),
        asset_type_id=asset_type.id,
        part_number="PN-COMP",
        serial_number="SN-COMP",
        nomenclature="Radar Component",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=org.id
    )
    db_session.add_all([org, asset_type, aircraft, component])
    db_session.commit()

    payload = {
        "aircraft_id": str(aircraft.id),
        "component_id": str(component.id),
        "failure_code": "RADAR-001",
        "severity": "CRITICAL",
        "description": "Radar screen blank in flight"
    }

    # Login to get JWT
    login_res = client.post("/api/v1/auth/login", json={"username": "chief_maintenance", "password": "any"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/maintenance/report-failure", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["grounding_applied"] is True
    assert data["aircraft_status"] == "GROUNDED"
    assert data["component_status"] == "GROUNDED"


def test_create_arsenal_request_endpoint(client, db_session):
    org = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    dep = Department(id=uuid4(), organization_id=org.id, name="Motores", department_type=DepartmentType.ENGINES)
    asset_type = AssetType(id=uuid4(), name="Aeronave", category="AIRCRAFT")
    component = Asset(
        id=uuid4(),
        asset_type_id=asset_type.id,
        part_number="PN-COMP",
        serial_number="SN-COMP",
        nomenclature="Radar Component",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=org.id
    )
    failure = FailureReport(
        id=uuid4(),
        asset_id=component.id,
        reported_by="Tech",
        failure_date=date.today(),
        description="Radar blank",
        severity=FailureSeverity.CRITICAL
    )
    db_session.add_all([org, dep, asset_type, component, failure])
    db_session.commit()

    payload = {
        "component_asset_id": str(component.id),
        "source_squadron_id": str(dep.id),
        "failure_report_id": str(failure.id),
        "requested_by": "Maintenance Chief",
        "priority": "HIGH"
    }

    # Login to get JWT
    login_res = client.post("/api/v1/auth/login", json={"username": "chief_maintenance", "password": "any"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/arsenal/create-request", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["component_status"] == "IN_TRANSFER"
    assert data["status"] == "CREATED"
