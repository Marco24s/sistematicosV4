import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.modules.organization.domain.models
import app.modules.assets.domain.models
import app.modules.maintenance.domain.models
from app.main import app
from app.core.database import Base, get_db
from app.modules.assets.domain.models import Asset, AssetType, AssetCondition, AssetStatus

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
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_new_endpoints(client, db_session):
    # Setup simple assets
    aircraft_type = AssetType(id=uuid4(), name="Helicopter", category="AIRCRAFT")
    db_session.add(aircraft_type)
    db_session.commit()
    
    aircraft = Asset(
        id=uuid4(),
        asset_type_id=aircraft_type.id,
        part_number="PN-1",
        serial_number="SN-1",
        nomenclature="Test Aircraft",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        classification="ROTABLE"
    )
    db_session.add(aircraft)
    db_session.commit()
    
    # 1. Login to get token
    login_res = client.post("/api/v1/auth/login", json={"username": "chief_maintenance", "password": "any"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Engine assemblies
    res = client.post("/api/v1/engine/assemblies", json={
        "asset_id": str(aircraft.id),
        "engine_model": "GE-T700",
        "serial_number": "ENG-SN-999"
    })
    assert res.status_code == 200, res.json()
    engine_assembly_id = res.json()["engine_assembly_id"]
    
    # Trend monitoring
    res_trend = client.post("/api/v1/engine/trend", json={
        "engine_assembly_id": engine_assembly_id,
        "turbine_temperature_c": 720.0,
        "oil_pressure_psi": 55.0,
        "vibration_level": 1.2
    })
    assert res_trend.status_code == 200
    
    # 3. Airworthiness evaluate
    res_air = client.get(f"/api/v1/airworthiness/evaluate/{aircraft.id}")
    assert res_air.status_code == 200
    
    # 4. LLP fatigue
    res_llp = client.get(f"/api/v1/llp/fatigue/{aircraft.id}")
    assert res_llp.status_code == 200
    
    # 5. Reporting
    res_rep = client.get("/api/v1/reporting/fleet-availability")
    assert res_rep.status_code == 200
    assert res_rep.json()["total_aircraft"] == 1
