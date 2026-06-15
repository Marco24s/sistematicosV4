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

        new_serial = "HP-" + str(uuid4())[:8]
        pump = Asset(
            id=uuid4(),
            asset_type_id=pump_type.id,
            part_number="HP-3321",
            serial_number=new_serial,
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
            
        mounted = MountedComponent(
            id=uuid4(),
            aircraft_configuration_id=config.id,
            asset_id=pump.id,
            position_code="HYD-SYS-1",
            installation_date=datetime.utcnow(),
            installed_by="tech",
            status=MountedComponentStatus.ACTIVE
        )
        db.add(mounted)
        db.commit()

        print(f"[SETUP] Created component {pump.nomenclature} ({new_serial}) mounted on {aircraft.nomenclature}")

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

        tech_user = db.query(SystemUser).filter_by(username="tech").first()
        dep = db.query(Department).first()

        print("\n[PASO 2] Remoción del Componente (MAF)")
        res = client.post("/api/v1/squadron/remove-component", headers=auth_h(token_jefe), json={
            "aircraft_id": str(aircraft.id),
            "component_id": str(pump.id),
            "removed_by": "tech",
            "actor_id": str(tech_user.id)
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Removido. Nuevo estado: UNSERVICEABLE")

        print("\n[PASO 3] Transferencia a Arsenal (PCP)")
        res = client.post("/api/v1/arsenal/create-request", headers=auth_h(token_jefe), json={
            "component_asset_id": str(pump.id),
            "source_squadron_id": str(dep.id),
            "requested_by": str(tech_user.id),
            "failure_report_id": failure_id,
            "priority": "CRITICAL"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        req_data = res.json()
        maint_req_id = req_data["maintenance_request_id"]
        print(f"-> Enviado a Arsenal. Request ID: {maint_req_id}")

        print("\n[PASO 4] Recepción en Pañol Arsenal")
        res = client.post("/api/v1/arsenal/receive-component", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "receiving_department_id": str(dep.id),
            "received_by_id": str(tech_user.id),
            "condition_notes": "Recibido embalado, con fugas visibles",
            "documentation_complete": True,
            "failure_report_code": "FR-HYD-001",
            "maf_code": "MAF-HP-001"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Recibido en Arsenal.")

        print("\n[PASO 5] Creación de Revisión de Ingeniería")
        res = client.post("/api/v1/engineering/create-review", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "assigned_engineer_id": str(tech_user.id),
            "priority": "HIGH"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        review_id = res.json()["engineering_review_id"]

        print("\n[PASO 5B] Dictamen Técnico de Ingeniería")
        res = client.post("/api/v1/engineering/technical-decision", headers=auth_h(token_jefe), json={
            "engineering_review_id": review_id,
            "decision": "REPAIR",
            "justification": "Sello axial fracturado",
            "technical_instruction": "ENG-INST-HP-99",
            "estimated_man_hours": 4.5
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Engineering Decision emitida: REPAIR")

        print("\n[PASO 6] Ejecución en Taller (Start Repair)")
        res = client.post("/api/v1/technical-section/start-repair", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "assigned_workshop_id": str(dep.id),
            "assigned_technician_id": str(tech_user.id)
        })
        assert res.status_code == 200, f"Error: {res.text}"
        rep_data = res.json()
        task_id = rep_data["repair_task_id"]
        print(f"-> Reparación iniciada en taller. Task ID: {task_id}")

        print("\n[PASO 7] Reparación Finalizada")
        res = client.post("/api/v1/technical-section/complete-repair", headers=auth_h(token_jefe), json={
            "repair_task_id": task_id,
            "action_taken": "Reemplazo sello.",
            "parts_replaced": ["SEAL-991"],
            "total_man_hours": 4.5,
            "remarks": "Prueba en banco hidráulico exitosa"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Componente enviado a Calidad.")

        print("\n[PASO 8] Aseguramiento de Calidad")
        res = client.post("/api/v1/quality/approve-repair", headers=auth_h(token_insp), json={
            "repair_task_id": task_id,
            "inspector_id": str(tech_user.id),
            "passed_inspection": True,
            "findings": "Banco de pruebas OK.",
            "certificate_code": "QI-HP-999"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Calidad aprobó.")

        print("\n[PASO 9] Emisión de Service Release (SRC)")
        res = client.post("/api/v1/arsenal/release-component", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "released_by_id": str(tech_user.id),
            "destination_department_id": str(dep.id),
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

        print("\nE2E SIMULATION FINISHED SUCCESSFULLY.")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_e2e()
