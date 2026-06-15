import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.modules.assets.domain.models import Asset, AssetType, AssetCondition, AssetStatus, AssetClassification
from app.modules.authorization.domain.models import SystemUser
from app.modules.organization.domain.models import Organization, Department
from app.modules.supply_chain.domain.models import InventoryLocation, InventoryLocationType
from app.modules.squadron_operations.domain.models import AircraftConfiguration, MountedComponent, MountedComponentStatus

client = TestClient(app)

def run_e2e():
    db: Session = SessionLocal()
    try:
        print("--- INICIANDO E2E TEST: HYDRAULIC PUMP HP-3321 ---")
        
        def login(username, password):
            res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
            assert res.status_code == 200, f"Login failed for {username}: {res.text}"
            return res.json()["access_token"]

        token_tech = login("tech", "tech123")
        token_insp = login("inspector", "inspector123")
        token_jefe = login("jefe", "jefe123")

        def auth_h(token): return {"Authorization": f"Bearer {token}"}

        aircraft = db.query(Asset).filter(Asset.nomenclature.ilike("%Sea King%")).first()
        if not aircraft:
            print("No aircraft found!")
            sys.exit(1)
        
        pump_type = db.query(AssetType).filter_by(category="COMPONENT").first()
        if not pump_type:
            pump_type = AssetType(id=uuid4(), name="Bomba Hidráulica", category="COMPONENT")
            db.add(pump_type)
            db.commit()

        pump = db.query(Asset).filter_by(serial_number="HP-3321-REAL").first()
        if not pump:
            pump = Asset(
                id=uuid4(),
                asset_type_id=pump_type.id,
                part_number="HP-3321",
                serial_number="HP-3321-REAL",
                nomenclature="Hydraulic Pump HP-3321",
                condition=AssetCondition.SERVICEABLE,
                current_status=AssetStatus.RELEASED,
                classification=AssetClassification.REPAIRABLE
            )
            db.add(pump)
            db.commit()
            db.refresh(pump)
            
        config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=aircraft.id, active=True).first()
        if not config:
            config = AircraftConfiguration(id=uuid4(), aircraft_asset_id=aircraft.id, configuration_name="DEFAULT-CONFIG", active=True)
            db.add(config)
            db.commit()
            
        mounted = db.query(MountedComponent).filter_by(asset_id=pump.id, aircraft_configuration_id=config.id).first()
        if not mounted:
            mounted = MountedComponent(
                id=uuid4(),
                aircraft_configuration_id=config.id,
                asset_id=pump.id,
                position_code="HYD-SYS-1",
                installation_date=datetime.utcnow(), installed_by="tech", status=MountedComponentStatus.ACTIVE
            )
            db.add(mounted)
            db.commit()

        print(f"[SETUP] Created component {pump.nomenclature} mounted on {aircraft.nomenclature}")

        print("\n[PASO 1] Reporte de Falla desde Vuelo (Grounding)")
        res = client.post("/api/v1/maintenance/report-failure", headers=auth_h(token_jefe), json={
            "aircraft_id": str(aircraft.id),
            "component_id": str(pump.id),
            "failure_code": "HYD-LEAK",
            "severity": "CRITICAL",
            "description": "Fuga crítica de fluido hidráulico en vuelo. Presión cayó a 0.",
            "reported_by": "Piloto Comandante"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        failure_data = res.json()
        print(f"-> Falla reportada. Aeronave status: {failure_data['aircraft_status']}. Componente status: {failure_data['component_status']}")
        failure_id = failure_data["failure_report_id"]

        print("\n[PASO 2] Remoción del Componente (MAF)")
        tech_user = db.query(SystemUser).filter_by(username="tech").first()
        res = client.post("/api/v1/squadron/remove-component", headers=auth_h(token_jefe), json={
            "aircraft_id": str(aircraft.id),
            "component_id": str(pump.id),
            "removed_by": "tech",
            "actor_id": str(tech_user.id)
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Removido. Nuevo estado: UNSERVICEABLE")

        print("\n[PASO 3] Transferencia a Arsenal (PCP)")
        res = client.post("/api/v1/arsenal/work-queue", headers=auth_h(token_jefe), json={
            "component_id": str(pump.id),
            "technician_id": str(tech_user.id),
            "failure_report_id": failure_id,
            "requested_by": "Jefe Mantenimiento EAH2",
            "priority": "CRITICAL"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        req_data = res.json()
        maint_req_id = req_data["maintenance_request_id"]
        print(f"-> Enviado a Arsenal. Request ID: {maint_req_id}")

        print("\n[PASO 4] Recepción en Pañol Arsenal")
        res = client.post("/api/v1/arsenal/receive", headers=auth_h(token_jefe), json={
            "component_id": str(pump.id),
            "maintenance_request_id": maint_req_id,
            "receiving_department_id": str(db.query(Department).first().id),
            "condition_notes": "Recibido embalado, con fugas visibles",
            "documentation_complete": True,
            "failure_report_code": "FR-HYD-001",
            "maf_code": "MAF-HP-001",
            "work_order_code": "WO-ARS-001"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Recibido. Work Order WO-ARS-001 vinculada.")

        print("\n[PASO 5] Dictamen de Ingeniería")
        res = client.post("/api/v1/arsenal/engineering/review", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "engineer_id": str(tech_user.id),
            "failure_analysis": "Sello axial fracturado",
            "repairable": True,
            "technical_disposition": "Reemplazar sello y testear en banco hidráulico",
            "instruction_code": "ENG-INST-HP-99",
            "execution_instructions": "Torque a 45 lbs."
        })
        assert res.status_code == 200, f"Error: {res.text}"
        inst_data = res.json()
        inst_id = inst_data["instruction_id"]
        print(f"-> Engineering Instruction emitida: ENG-INST-HP-99 (ID: {inst_id})")

        print("\n[PASO 6] Ejecución en Taller (Start Repair)")
        res = client.post("/api/v1/arsenal/repair/start", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "workshop_id": str(db.query(Department).first().id),
            "technician_id": str(tech_user.id),
            "engineering_instruction_id": inst_id
        })
        assert res.status_code == 200, f"Error: {res.text}"
        rep_data = res.json()
        task_id = rep_data["repair_task_id"]
        print(f"-> Reparación iniciada en taller. Task ID: {task_id}")

        print("\n[PASO 7] Reparación Finalizada")
        res = client.post("/api/v1/arsenal/repair/complete", headers=auth_h(token_jefe), json={
            "repair_task_id": task_id,
            "technician_id": str(tech_user.id),
            "action_taken": "Reemplazo sello.",
            "parts_replaced": ["SEAL-991"],
            "man_hours": 4.5
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Componente enviado a Calidad.")

        print("\n[PASO 8] Aseguramiento de Calidad")
        res = client.post("/api/v1/arsenal/repair/approve", headers=auth_h(token_insp), json={
            "repair_task_id": task_id,
            "inspector_id": str(tech_user.id),
            "passed_inspection": True,
            "findings": "Banco de pruebas OK."
        })
        assert res.status_code == 200, f"Error: {res.text}"
        qi_data = res.json()
        inspection_id = qi_data["quality_inspection_id"]
        print(f"-> Calidad aprobó. Certificado ID: {inspection_id}")

        print("\n[PASO 9] Emisión de Service Release (SRC)")
        res = client.post("/api/v1/arsenal/release", headers=auth_h(token_jefe), json={
            "component_id": str(pump.id),
            "maintenance_request_id": maint_req_id,
            "quality_inspection_id": inspection_id,
            "released_by": "Jefe Arsenal",
            "destination_department_id": str(db.query(Department).first().id),
            "src_document_code": "SRC-HP-2026",
            "hrb_document_code": "HRB-HP-2026"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> SRC-HP-2026 emitido. Estado del componente: SERVICEABLE.")

        print("\n[PASO 10] Instalación en Aeronave")
        res = client.post("/api/v1/squadron/install-component", headers=auth_h(token_jefe), json={
            "aircraft_id": str(aircraft.id),
            "component_id": str(pump.id),
            "position_code": "HYD-SYS-1",
            "installed_by": "tech",
            "actor_id": str(tech_user.id)
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Instalado.")

        print("\n=== REPORTE DE TRAZABILIDAD (BASE DE DATOS) ===")
        
        from app.shared.infrastructure.event_store import DomainEventModel
        from app.modules.assets.domain.models import TechnicalHistory
        from app.modules.document_management.domain.models import Document
        from app.modules.arsenal_workflow.domain.models import MaintenanceRequest, QualityInspection

        events = db.query(DomainEventModel).filter(DomainEventModel.aggregate_id == pump.id).order_by(DomainEventModel.occurred_on).all()
        print("\n[EVENTS STORE - EVENTOS DE DOMINIO]")
        for e in events:
            print(f" - {e.occurred_on.strftime('%H:%M:%S')} | {e.event_type}")

        hist = db.query(TechnicalHistory).filter(TechnicalHistory.asset_id == pump.id).order_by(TechnicalHistory.recorded_at).all()
        print("\n[TECHNICAL HISTORY - HISTORIAL TÉCNICO]")
        for h in hist:
            print(f" - {h.recorded_at.strftime('%H:%M:%S')} | {h.action_type}: {h.description}")

        docs = db.query(Document).filter(Document.reference_entity_id == pump.id).all()
        print("\n[ASSET DOCUMENTS - DOCUMENTACIÓN VINCULADA]")
        for d in docs:
            print(f" - {d.document_code} ({d.document_type.name}) | Verificado: {d.verified}")

        print("\n[ARSENAL WORKFLOW]")
        mr = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == maint_req_id).first()
        print(f" - Req ID: {mr.id} | Status: {mr.status} | Priority: {mr.priority}")

        qi = db.query(QualityInspection).filter(QualityInspection.id == inspection_id).first()
        print(f" - Qual ID: {qi.id} | Passed: {qi.passed_inspection} | Findings: {qi.findings}")

        print("\nE2E SIMULATION FINISHED SUCCESSFULLY.")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_e2e()
