import pytest
import sqlite3
from datetime import date, datetime, timedelta, timezone
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
import app.modules.tool_calibration.domain.models
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
import app.modules.authorization.domain.models

from app.main import app
from app.core.database import Base, get_db
from app.modules.organization.domain.models import Organization, OrganizationType, Department, DepartmentType
from app.modules.assets.domain.models import Asset, AssetType, TechnicalHistory, AssetStatus, AssetCondition, AssetClassification
from app.modules.maintenance.domain.models import FailureReport, FailureSeverity, MaintenanceCounter
from app.modules.arsenal_workflow.domain.models import MaintenanceRequest
from app.modules.squadron_operations.domain.models import AircraftConfiguration, MountedComponent, MountedComponentStatus
from app.modules.personnel_certification.domain.models import (
    TechnicianProfile,
    TechnicianCertification,
    CertificationLevel,
    CertificationMinimumLevel,
    CertificationRequirement,
    TechnicalSpecialization,
)
from app.modules.authorization.domain.models import DigitalSignatureCertificate
from app.modules.tool_calibration.domain.models import Tool, CalibrationCertificate

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

def test_full_operational_cycle(client, db_session):
    # ==========================================
    # 1. SETUP DE DATOS E HISTORIAL INICIAL
    # ==========================================
    
    # Organizaciones y Departamentos
    comando = Organization(id=uuid4(), name="Comando Aviación Naval", organization_type=OrganizationType.ARSENAL)
    squadron = Organization(id=uuid4(), name="Segunda Escuadrilla Aeronaval de Helicópteros", organization_type=OrganizationType.SQUADRON)
    db_session.add_all([comando, squadron])
    db_session.commit()
    
    squadron_dept = Department(id=uuid4(), organization_id=squadron.id, name="Motores", department_type=DepartmentType.ENGINES)
    arsenal_dept = Department(id=uuid4(), organization_id=comando.id, name="Arsenal Calidad", department_type=DepartmentType.QUALITY)
    db_session.add_all([squadron_dept, arsenal_dept])
    db_session.commit()
    
    # Tipos de Activo
    aircraft_type = AssetType(id=uuid4(), name="Helicoptero", category="AIRCRAFT")
    component_type = AssetType(id=uuid4(), name="Servo Hidraulico", category="HYDRAULIC_COMPONENT")
    db_session.add_all([aircraft_type, component_type])
    db_session.commit()
    
    # Activos (Sea King y Componente)
    sea_king = Asset(
        id=uuid4(),
        asset_type_id=aircraft_type.id,
        part_number="SH-3D",
        serial_number="2-H-231",
        nomenclature="Sikorsky Sea King",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED,
        current_custodian_id=squadron_dept.id,
        classification=AssetClassification.ROTABLE,
    )
    servo = Asset(
        id=uuid4(),
        asset_type_id=component_type.id,
        part_number="PN-HYD-77",
        serial_number="SN-SV-007",
        nomenclature="Primary Hydraulic Servo",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.INSTALLED,
        current_custodian_id=squadron_dept.id,
        classification=AssetClassification.REPAIRABLE,
    )
    db_session.add_all([sea_king, servo])
    db_session.commit()
    
    # Historiales Técnicos
    sk_history = TechnicalHistory(
        id=uuid4(),
        asset_id=sea_king.id,
        opened_date=date.today(),
        current_total_hours=Decimal("1500.0"),
        current_total_cycles=320,
    )
    servo_history = TechnicalHistory(
        id=uuid4(),
        asset_id=servo.id,
        opened_date=date.today(),
        current_total_hours=Decimal("45.0"),
        current_total_cycles=12,
    )
    db_session.add_all([sk_history, servo_history])
    db_session.commit()
    
    # Configuración de Aeronave Activa y Montaje
    config = AircraftConfiguration(
        id=uuid4(),
        aircraft_asset_id=sea_king.id,
        configuration_name="Standard Sea King",
        active=True
    )
    db_session.add(config)
    db_session.commit()
    
    mounted = MountedComponent(
        id=uuid4(),
        aircraft_configuration_id=config.id,
        asset_id=servo.id,
        position_code="HYDRAULIC_SLOT",
        installation_date=datetime.utcnow(),
        installed_by="Mecanico Principal",
        status=MountedComponentStatus.ACTIVE,
    )
    db_session.add(mounted)
    db_session.commit()
    
    # Contadores de Mantenimiento iniciales
    counter_sk = MaintenanceCounter(
        id=uuid4(),
        asset_id=sea_king.id,
        maintenance_program_id=uuid4(),
        current_usage=1500,
        remaining_usage=100
    )
    counter_servo = MaintenanceCounter(
        id=uuid4(),
        asset_id=servo.id,
        maintenance_program_id=uuid4(),
        current_usage=45,
        remaining_usage=55
    )
    db_session.add_all([counter_sk, counter_servo])
    db_session.commit()
    
    # Personal y Certificaciones (Técnico Habilitado)
    tech = TechnicianProfile(
        id=uuid4(),
        personnel_id=uuid4(),
        technical_code="T-801",
        join_date=date.today() - timedelta(days=500),
        current_level=CertificationLevel.LEVEL_B,
        years_of_experience=Decimal("3.5"),
        active=True
    )
    specialization = TechnicalSpecialization(id=uuid4(), name="HYDRAULIC_SYSTEMS", description="Especialista Hidráulica")
    db_session.add_all([tech, specialization])
    db_session.commit()
    
    tech_cert = TechnicianCertification(
        id=uuid4(),
        technician_profile_id=tech.id,
        specialization_id=specialization.id,
        certification_level=CertificationLevel.LEVEL_B,
        issued_date=date.today() - timedelta(days=100),
        expiration_date=date.today() + timedelta(days=200),
        issued_by="Comando Calidad",
        active=True
    )
    db_session.add(tech_cert)
    db_session.commit()
    
    # Personal de Inspección de Calidad (Inspector Habilitado)
    inspector = TechnicianProfile(
        id=uuid4(),
        personnel_id=uuid4(),
        technical_code="I-901",
        join_date=date.today() - timedelta(days=1000),
        current_level=CertificationLevel.INSPECTOR,
        years_of_experience=Decimal("8.0"),
        active=True
    )
    inspector_cert = TechnicianCertification(
        id=uuid4(),
        technician_profile_id=inspector.id,
        specialization_id=specialization.id,
        certification_level=CertificationLevel.INSPECTOR,
        issued_date=date.today() - timedelta(days=200),
        expiration_date=date.today() + timedelta(days=300),
        issued_by="Comando Calidad",
        active=True
    )
    inspector_sig = DigitalSignatureCertificate(
        id=uuid4(),
        user_id=inspector.id,
        certificate_serial="SIG-INSP-901",
        issued_at=datetime.utcnow() - timedelta(days=10),
        expires_at=datetime.utcnow() + timedelta(days=350),
        active=True
    )
    db_session.add_all([inspector, inspector_cert, inspector_sig])
    db_session.commit()
    
    # Herramienta calibrada
    tool = Tool(id=uuid4(), tool_serial="TQ-M-112", name="Torquimetro Digital", active=True)
    tool_cal = CalibrationCertificate(
        id=uuid4(),
        tool_id=tool.id,
        calibration_date=date.today() - timedelta(days=10),
        calibration_due_date=date.today() + timedelta(days=170),
        certification_document_code="CERT-CAL-112"
    )
    db_session.add_all([tool, tool_cal])
    db_session.commit()
    # Login as maintenance chief to generate JWT for protected actions
    login_res = client.post("/api/v1/auth/login", json={"username": "chief_maintenance", "password": "any"})
    assert login_res.status_code == 200, login_res.json()
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ==========================================
    # 2. CIERRE DE VUELO (CLOSE FLIGHT)
    # ==========================================
    flight_payload = {
        "aircraft_id": str(sea_king.id),
        "flight_hours": 2.5
    }
    res_flight = client.post("/api/v1/flight/close", json=flight_payload, headers=headers)
    assert res_flight.status_code == 200, res_flight.json()
    data_flight = res_flight.json()
    assert data_flight["aircraft"]["total_hours"] == 1502.5
    
    # ==========================================
    # 3. REPORTE DE FALLA (GROUNDING AUTOMÁTICO)
    # ==========================================
    failure_payload = {
        "aircraft_id": str(sea_king.id),
        "component_id": str(servo.id),
        "failure_code": "HYD-LEAK",
        "severity": "CRITICAL",
        "description": "Fuga crítica de fluido hidráulico observada en conector primario.",
        "reported_by": "Jefe Escuadrilla"
    }
    res_fail = client.post("/api/v1/maintenance/report-failure", json=failure_payload, headers=headers)
    assert res_fail.status_code == 200, res_fail.json()
    data_fail = res_fail.json()
    assert data_fail["aircraft_status"] == "GROUNDED"
    assert data_fail["grounding_applied"] is True
    
    failure_report_id = data_fail["failure_report_id"]
    
    # ==========================================
    # 4. CREAR SOLICITUD DE TRANSFERENCIA ARSENAL
    # ==========================================
    req_payload = {
        "component_asset_id": str(servo.id),
        "source_squadron_id": str(squadron_dept.id),
        "failure_report_id": failure_report_id,
        "requested_by": "Jefe Mantenimiento",
        "priority": "HIGH",
        "actor_id": "chief-squadron"
    }
    res_req = client.post("/api/v1/arsenal/create-request", json=req_payload, headers=headers)
    assert res_req.status_code == 200, res_req.json()
    data_req = res_req.json()
    assert data_req["component_status"] == "IN_TRANSFER"
    
    maintenance_request_id = data_req["maintenance_request_id"]
    
    # ==========================================
    # 5. REMOVER COMPONENTE DE LA AERONAVE
    # ==========================================
    remove_payload = {
        "aircraft_id": str(sea_king.id),
        "component_id": str(servo.id),
        "removed_by": "Mecanico 1"
    }
    res_remove = client.post("/api/v1/squadron/remove-component", json=remove_payload)
    assert res_remove.status_code == 200, res_remove.json()
    data_remove = res_remove.json()
    assert data_remove["status"] == "removed"
    assert data_remove["component_condition"] == "UNSERVICEABLE"
    
    # ==========================================
    # 6. TRANSFERENCIA FÍSICA A ALMACÉN ESCUADRÓN / ARSENAL
    # ==========================================
    transfer_payload = {
        "component_id": str(servo.id),
        "destination_department_id": str(arsenal_dept.id),
        "performed_by": "Pañolero Escuadrón"
    }
    res_transfer = client.post("/api/v1/supply-chain/transfer-to-squadron-storage", json=transfer_payload)
    assert res_transfer.status_code == 200, res_transfer.json()
    
    # ==========================================
    # 7. RECEPCIÓN EN EL ARSENAL Y VALIDACIÓN
    # ==========================================
    receive_payload = {
        "component_id": str(servo.id),
        "maintenance_request_id": maintenance_request_id,
        "received_by_department_id": str(arsenal_dept.id),
        "condition_notes": "Sello dañado visible. Conector sucio.",
        "documentation_complete": True
    }
    res_receive = client.post("/api/v1/arsenal/receive-component", json=receive_payload)
    assert res_receive.status_code == 200, res_receive.json()
    data_receive = res_receive.json()
    assert data_receive["status"] == "RECEIVED"
    assert data_receive["documentation_complete"] is True
    
    # ==========================================
    # 8. INGENIERÍA: CREACIÓN DE REVISIÓN E INSTRUCCIÓN
    # ==========================================
    review_payload = {
        "maintenance_request_id": maintenance_request_id,
        "engineer_id": str(inspector.id),
        "failure_analysis": "Fatiga de material elastómero en el retén.",
        "repairable": True,
        "recommended_action": "Cambio de kit de juntas tóricas y prueba de presión.",
        "instruction_code": "ING-HYD-551",
        "procedure_description": "Desarme primario, limpieza por ultrasonido, cambio de O-rings."
    }
    res_review = client.post("/api/v1/engineering/create-review", json=review_payload)
    assert res_review.status_code == 200, res_review.json()
    data_review = res_review.json()
    assert data_review["review_status"] == "APPROVED"
    assert data_review["instruction_id"] is not None
    
    instruction_id = data_review["instruction_id"]
    
    # Pre-crear requerimiento de especialización de personal para validar start repair
    req_cert = CertificationRequirement(
        id=uuid4(),
        task_type=str(maintenance_request_id),
        required_specialization_id=specialization.id,
        minimum_level=CertificationMinimumLevel.LEVEL_B,
        requires_inspector_approval=False
    )
    db_session.add(req_cert)
    db_session.commit()
    
    # ==========================================
    # 9. INICIO DE REPARACIÓN
    # ==========================================
    repair_payload = {
        "maintenance_request_id": maintenance_request_id,
        "assigned_section_id": str(arsenal_dept.id),
        "assigned_technician_id": str(tech.id),
        "instruction_id": instruction_id,
        "tool_id": str(tool.id)
    }
    res_repair = client.post("/api/v1/technical-section/start-repair", json=repair_payload, headers=headers)
    assert res_repair.status_code == 200, res_repair.json()
    data_repair = res_repair.json()
    assert data_repair["status"] == "IN_PROGRESS"
    
    repair_task_id = data_repair["repair_task_id"]
    
    # ==========================================
    # 10. APROBACIÓN DE CALIDAD E INSPECCIÓN
    # ==========================================
    approve_payload = {
        "repair_task_id": repair_task_id,
        "inspector_id": str(inspector.id),
        "is_critical": False
    }
    res_approve = client.post("/api/v1/quality/approve-repair", json=approve_payload, headers=headers)
    assert res_approve.status_code == 200, res_approve.json()
    data_approve = res_approve.json()
    assert data_approve["status"] == "APPROVED"
    
    quality_inspection_id = data_approve["quality_inspection_id"]
    
    # ==========================================
    # 11. LIBERACIÓN TÉCNICA (RELEASE COMPONENT)
    # ==========================================
    release_payload = {
        "component_id": str(servo.id),
        "maintenance_request_id": maintenance_request_id,
        "quality_inspection_id": quality_inspection_id,
        "released_by": "Jefe Calidad Arsenal",
        "returned_to_department_id": str(squadron_dept.id)
    }
    res_release = client.post("/api/v1/arsenal/release-component", json=release_payload)
    assert res_release.status_code == 200, res_release.json()
    data_release = res_release.json()
    assert data_release["status"] == "SERVICEABLE"
    assert data_release["component_condition"] == "SERVICEABLE"
    assert data_release["component_status"] == "IN_STOCK"
    
    # ==========================================
    # 12. INSTALACIÓN DE VUELTA Y APROBACIÓN DE VUELO
    # ==========================================
    install_payload = {
        "aircraft_id": str(sea_king.id),
        "component_id": str(servo.id),
        "position_code": "HYDRAULIC_SLOT",
        "installed_by": "Mecanico Escuadrilla"
    }
    res_install = client.post("/api/v1/squadron/install-component", json=install_payload, headers=headers)
    assert res_install.status_code == 200, res_install.json()
    data_install = res_install.json()
    assert data_install["aircraft_status"] == "RELEASED"
    assert data_install["is_airworthy"] is True
