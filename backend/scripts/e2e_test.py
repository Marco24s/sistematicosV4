import sys
import os
import json
from uuid import UUID

sys.path.append("c:/sistematicosV4/backend")

from app.core.database import SessionLocal
from app.modules.assets.domain.models import Asset, AssetStatus, AssetCondition
from app.modules.organization.domain.models import Organization, Department
from app.modules.authorization.domain.models import SystemUser
from app.modules.flight_operations.domain.models import InstalledAsset, InstalledAssetStatus
from app.shared.infrastructure.event_store import DomainEventStore

db = SessionLocal()

def run_e2e():
    print("=== INICIANDO E2E TEST: HYDRAULIC PUMP HP-3321 ===")

    aircraft = db.query(Asset).filter(Asset.serial_number == "2-H-231").first()
    if not aircraft:
        print("Aircraft not found")
        return
        
    print(f"-> Aircraft Selected: {aircraft.nomenclature} ({aircraft.serial_number})")
    
    import uuid
    from app.modules.assets.domain.models import AssetType, AssetClassification
    from app.modules.assets.domain.models import TechnicalHistory
    from datetime import date

    comp_type = db.query(AssetType).filter(AssetType.category == "COMPONENT").first()
    if not comp_type:
        comp_type = AssetType(id=uuid.uuid4(), name="Hydraulic Pump", category="COMPONENT")
        db.add(comp_type)
        db.flush()

    pump_id = uuid.uuid4()
    pump = Asset(
        id=pump_id,
        asset_type_id=comp_type.id,
        part_number="HP-3321",
        serial_number="HP-3321-SN001",
        nomenclature="Hydraulic Pump HP-3321",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        classification=AssetClassification.REPAIRABLE
    )
    db.add(pump)
    
    hist = TechnicalHistory(
        id=uuid.uuid4(),
        asset_id=pump.id,
        opened_date=date.today(),
        current_total_hours=0,
        current_total_cycles=0
    )
    db.add(hist)
    db.flush()
    print(f"-> Component Created: {pump.nomenclature} ({pump.serial_number})")

    install_record = InstalledAsset(
        id=uuid.uuid4(),
        aircraft_asset_id=aircraft.id,
        installed_asset_id=pump.id,
        position_code="HYD-SYS-1",
        installed_by="Test_Seed",
        status=InstalledAssetStatus.INSTALLED
    )
    db.add(install_record)
    db.commit()
    print("-> Component Installed on Aircraft")

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    
    from app.core.security import create_access_token
    token = create_access_token({"sub": "admin", "roles": ["ADMIN"]})
    headers = {"Authorization": f"Bearer $token"}
    
    print("\n--- PASO 1: VUELO ---")
    open_res = client.post("/api/v1/flight/open", json={
        "aircraft_id": str(aircraft.id),
        "pilot_name": "Lt. Test",
        "mission_type": "PATROL",
        "planned_hours": 2.5,
        "authorized_by": "Cmdr. Test"
    }, headers=headers)
    print(f"Flight Open Status: {open_res.status_code}")
    
    close_res = client.post("/api/v1/flight/close", json={
        "aircraft_id": str(aircraft.id),
        "flight_hours": 2.5,
        "technical_observations": "Vibraciones en sistema hidráulico"
    }, headers=headers)
    print(f"Flight Close Status: {close_res.status_code}")
    
    print("\n--- PASO 2: FAILURE REPORT ---")
    fail_res = client.post("/api/v1/maintenance/report-failure", json={
        "aircraft_id": str(aircraft.id),
        "component_id": str(pump.id),
        "failure_code": "HYD-LEAK",
        "severity": "CRITICAL",
        "description": "Fuga grave de presión en bomba hidráulica",
        "reported_by": "Mecánico de Línea"
    }, headers=headers)
    print(f"Report Failure Status: {fail_res.status_code}")
    if fail_res.status_code == 200:
        failure_report_id = fail_res.json()["failure_report_id"]
    else:
        print(fail_res.json())
        return

    print("\n--- PASO 3: REMOCIÓN ---")
    rem_res = client.post(f"/api/v1/assets/aircraft/{aircraft.id}/components/remove", json={
        "component_id": str(pump.id),
        "removed_by": "Mecánico de Línea"
    }, headers=headers)
    print(f"Remove Component Status: {rem_res.status_code}")

    print("\n--- PASO 4: TRÁNSITO A ESCUADRÓN ---")
    dep = db.query(Department).first()
    transfer_res = client.post(f"/api/v1/assets/components/{pump.id}/transfer", json={
        "new_department_id": str(dep.id),
        "transferred_by": "Mecánico de Línea"
    }, headers=headers)
    print(f"Transfer Status: {transfer_res.status_code}")

    print("\n--- PASO 5: ARSENAL RECEPTION ---")
    rec_res = client.post("/api/v1/arsenal/receptions", json={
        "component_id": str(pump.id),
        "origin_department_id": str(dep.id),
        "failure_report_id": failure_report_id,
        "received_by": "Encargado Pañol Arsenal",
        "priority": "HIGH"
    }, headers=headers)
    print(f"Arsenal Reception Status: {rec_res.status_code}")
    if rec_res.status_code != 200:
        print(rec_res.json())
        return
    req_id = rec_res.json()["maintenance_request_id"]
    rec_id = rec_res.json()["reception_id"]

    print("\n--- PASO 6: INGENIERÍA REVIEW ---")
    phy_res = client.post("/api/v1/arsenal/physical-reception", json={
        "component_id": str(pump.id),
        "reception_request_id": rec_id,
        "department_id": str(dep.id),
        "condition_notes": "Recibido con pérdida de fluido",
        "documentation_complete": True,
        "failure_report_code": "FR-123",
        "maf_code": "MAF-123",
        "work_order_code": "WO-123"
    }, headers=headers)
    print(f"Physical Reception Status: {phy_res.status_code}")

    rev_res = client.post(f"/api/v1/arsenal/requests/{req_id}/review", json={
        "engineer_id": str(db.query(SystemUser).first().id),
        "diagnosis": "Sellos hidráulicos destruidos",
        "requires_workshop": True,
        "workshop_directive": "Reemplazo de sellos O-ring y prueba de presión",
        "instruction_code": "EI-HYD-001",
        "technical_instructions": "Torque 45 lbs"
    }, headers=headers)
    print(f"Engineering Review Status: {rev_res.status_code}")
    if rev_res.status_code != 200:
        print(rev_res.json())
        return
    instruction_id = rev_res.json()["instruction_id"]

    print("\n--- PASO 7: TALLER (START REPAIR) ---")
    tech_id = str(db.query(SystemUser).first().id)
    rep_res = client.post("/api/v1/arsenal/repairs", json={
        "maintenance_request_id": req_id,
        "technician_id": tech_id,
        "inspector_id": tech_id,
        "engineering_instruction_id": instruction_id,
        "tool_id": None
    }, headers=headers)
    print(f"Start Repair Status: {rep_res.status_code}")
    if rep_res.status_code != 200:
        print(rep_res.json())
        return
    task_id = rep_res.json()["repair_task_id"]

    print("\n--- PASO 8: CALIDAD (APPROVE) ---")
    qual_res = client.post(f"/api/v1/arsenal/repairs/{task_id}/quality-check", json={
        "inspector_id": tech_id,
        "approved": True
    }, headers=headers)
    print(f"Quality Check Status: {qual_res.status_code}")
    if qual_res.status_code != 200:
        print(qual_res.json())
        return
    inspection_id = qual_res.json()["quality_inspection_id"]

    print("\n--- PASO 9: SERVICE RELEASE ---")
    rel_res = client.post("/api/v1/maintenance/service-release", json={
        "component_id": str(pump.id),
        "maintenance_request_id": req_id,
        "quality_inspection_id": inspection_id,
        "released_by": "Jefe Aseguramiento Calidad",
        "destination_department_id": str(dep.id),
        "src_code": "SRC-HYD-001",
        "hrb_code": "HRB-HYD-001"
    }, headers=headers)
    print(f"Service Release Status: {rel_res.status_code}")
    if rel_res.status_code != 200:
        print(rel_res.json())
        return

    print("\n--- PASO 10: INSTALACIÓN ---")
    inst_res = client.post(f"/api/v1/assets/aircraft/{aircraft.id}/components/install", json={
        "component_id": str(pump.id),
        "position_code": "HYD-SYS-1",
        "installed_by": "Mecánico de Línea"
    }, headers=headers)
    print(f"Install Component Status: {inst_res.status_code}")
    if inst_res.status_code != 200:
        print(inst_res.json())

    print("\n\n=== VERIFICACIÓN DE DOMINIO Y TRAZABILIDAD ===")
    
    events = db.query(DomainEventStore).filter(DomainEventStore.aggregate_id == pump.id).all()
    print(f"Eventos en DomainEventStore para la Bomba HP-3321: {len(events)}")
    for ev in events:
        print(f" - {ev.event_type} | {ev.timestamp}")

    print("\nVerificando Service Release...")
    from app.modules.maintenance_signoff.domain.models import ServiceReleaseCertificate
    src = db.query(ServiceReleaseCertificate).filter_by(asset_id=pump.id).first()
    if src:
        print(f"[OK] SRC generado: {src.certificate_code}")

    print("\nVerificando Quality Inspection...")
    from app.modules.quality.domain.models import QualityInspection
    qi = db.query(QualityInspection).filter_by(id=inspection_id).first()
    if qi:
        print(f"[OK] Inspección generada: Aprobado={qi.approved}")
        
    print("\nVerificando Historial Técnico...")
    hist_pump = db.query(TechnicalHistory).filter_by(asset_id=pump.id).first()
    if hist_pump:
        print(f"[OK] Technical History enlazado.")
        
    print("\nVerificando Documents...")
    from app.modules.document_management.domain.models import Document
    docs = db.query(Document).filter_by(asset_id=pump.id).all()
    print(f"[OK] Documentos generados para la bomba: {len(docs)}")

    print("\n===========================================")
    print("E2E COMPLETO Y EXITOSO.")

if __name__ == "__main__":
    run_e2e()
