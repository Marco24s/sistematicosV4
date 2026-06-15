import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.modules.assets.domain.models import AssetType
from app.modules.organization.domain.models import Organization

client = TestClient(app)
db = SessionLocal()

# 1. Login as admin
res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
if res.status_code != 200:
    print("Login failed", res.json())
    exit(1)
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Find AIRCRAFT asset type and an organization
aircraft_type = db.query(AssetType).filter_by(category="AIRCRAFT").first()
org = db.query(Organization).first()

if not aircraft_type or not org:
    print("Missing data")
    exit(1)

# 3. Register Aircraft
payload = {
    "serial_number": "TEST-AC-001",
    "asset_type_id": str(aircraft_type.id),
    "organization_id": str(org.id),
    "classification": "REPAIRABLE",
    "part_number": "PN-AIRCRAFT-TEST",
    "nomenclature": "Test Aircraft Commissioning",
    "origin_terminal": "TEST-SCRIPT"
}

res = client.post("/api/v1/assets/register", json=payload, headers=headers)
print("Register response:", res.status_code, res.json())

# 4. Verify Baseline and Documents
from app.modules.configuration_baseline.domain.models import AircraftBaselineConfiguration
from app.modules.document_management.domain.models import AssetDocument

if res.status_code == 200:
    asset_id = res.json()["id"]
    baselines = db.query(AircraftBaselineConfiguration).filter_by(aircraft_model_id=aircraft_type.id).all()
    print("Baselines found:", len(baselines))
    docs = db.query(AssetDocument).filter_by(asset_id=asset_id).all()
    print("Documents found:", len(docs), [d.title for d in docs])
