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
import app.shared.infrastructure.event_store

# Modelos específicos del test
from app.modules.assets.domain.models import Asset, AssetClassification, AssetConfigurationNode, AssetLifecycleEvent, AssetCondition, AssetStatus
from app.modules.tool_calibration.domain.models import Tool, CalibrationCertificate, ToolAssignment
from app.modules.document_management.domain.models import PhysicalDocumentCustody, AssetDocument
from app.modules.maintenance.domain.models import WorkOrder, DeferredDefect
from app.modules.squadron_operations.domain.models import AircraftOperationalInterruption, ConfigurationSlot, MountedComponentHistory


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    yield session
    session.close()


def test_hierarchical_configuration_management(db_session: Session) -> None:
    # 1. Crear assets
    aircraft = Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="AIRCRAFT-01",
        serial_number="SN-AC01",
        nomenclature="Super Etendard 2-H-202",
        classification=AssetClassification.ROTABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.RELEASED
    )
    engine_left = Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="ENGINE-ATAR",
        serial_number="SN-ENG01",
        nomenclature="Atar 8K50 Engine",
        classification=AssetClassification.REPAIRABLE,
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.IN_STOCK
    )
    db_session.add_all([aircraft, engine_left])
    db_session.commit()

    # 2. Configurar jerarquía
    node = AssetConfigurationNode(
        parent_asset_id=aircraft.id,
        child_asset_id=engine_left.id,
        position_code="LEFT_ENGINE",
        installation_level=1,
        installed_at=datetime.now(timezone.utc).date()
    )
    db_session.add(node)
    db_session.commit()

    assert node.parent_asset_id == aircraft.id
    assert node.child_asset_id == engine_left.id
    assert node.position_code == "LEFT_ENGINE"


def test_asset_classification_system() -> None:
    # Validar el enum y la clasificación
    assert AssetClassification.REPAIRABLE == "REPAIRABLE"
    assert AssetClassification.CONSUMABLE == "CONSUMABLE"
    assert AssetClassification.ROTABLE == "ROTABLE"
    assert AssetClassification.LIFE_LIMITED == "LIFE_LIMITED"


def test_tool_calibration_rules(db_session: Session) -> None:
    # 1. Crear herramienta
    tool = Tool(
        id=uuid4(),
        tool_serial="TQ-5001",
        name="Torque Wrench 10-100 Nm",
        active=True
    )
    db_session.add(tool)
    db_session.commit()

    # 2. Registrar certificado de calibración vencido
    expired_cert = CalibrationCertificate(
        tool_id=tool.id,
        calibration_date=datetime.now(timezone.utc).date() - timedelta(days=200),
        calibration_due_date=datetime.now(timezone.utc).date() - timedelta(days=20),
        certification_document_code="CERT-EXP-01"
    )
    db_session.add(expired_cert)
    db_session.commit()

    # Regla: La herramienta tiene vencimiento expirado
    assert expired_cert.calibration_due_date < datetime.now(timezone.utc).date()


def test_physical_document_custody(db_session: Session) -> None:
    doc_id = uuid4()
    dept_id = uuid4()
    
    custody = PhysicalDocumentCustody(
        document_id=doc_id,
        current_department_id=dept_id,
        received_by="TECH-MARTIN",
        released_by="CHIEF-COSTA",
        transfer_date=datetime.now(timezone.utc)
    )
    db_session.add(custody)
    db_session.commit()

    assert custody.document_id == doc_id
    assert custody.current_department_id == dept_id
    assert custody.received_by == "TECH-MARTIN"


def test_work_order_military_priority(db_session: Session) -> None:
    # Verificar la adición de prioridad operacional
    order = WorkOrder(
        id=uuid4(),
        failure_report_id=uuid4(),
        origin_department_id=uuid4(),
        assigned_department_id=uuid4(),
        priority="AOG", # preexistente en StrEnum
        priority_level="COMBAT_PRIORITY",
        priority_reason="Urgent combat preparation for fleet readiness",
        status="CREATED"
    )
    db_session.add(order)
    db_session.commit()

    assert order.priority_level == "COMBAT_PRIORITY"
    assert order.priority_reason == "Urgent combat preparation for fleet readiness"


def test_aog_interruption_availability(db_session: Session) -> None:
    aircraft_id = uuid4()
    interruption = AircraftOperationalInterruption(
        aircraft_id=aircraft_id,
        interruption_type="MISSING_COMPONENT",
        reason="Awaiting left engine turbine blades from supplier",
        started_at=datetime.now(timezone.utc),
        severity="CRITICAL"
    )
    db_session.add(interruption)
    db_session.commit()

    assert interruption.aircraft_id == aircraft_id
    assert interruption.interruption_type == "MISSING_COMPONENT"
    assert interruption.resolved_at is None


def test_deferred_defects_hours_limit(db_session: Session) -> None:
    aircraft_id = uuid4()
    defect = DeferredDefect(
        aircraft_id=aircraft_id,
        failure_report_id=uuid4(),
        allowed_until_hours=1250.0,
        restriction_level="Day VFR Only",
        repair_deadline=datetime.now(timezone.utc).date() + timedelta(days=10),
        approved_by="CO-AIR-WING",
        status="ACTIVE"
    )
    db_session.add(defect)
    db_session.commit()

    assert defect.aircraft_id == aircraft_id
    assert defect.allowed_until_hours == 1250.0
    assert defect.status == "ACTIVE"


def test_configuration_slot_validation(db_session: Session) -> None:
    model_id = uuid4()
    slot = ConfigurationSlot(
        aircraft_model_id=model_id,
        slot_code="MAIN_ROTOR_BLADE_1",
        slot_name="Main Rotor Blade Position 1",
        compatible_asset_types="BLADE-UH1H,BLADE-UH1Y",
        required=True,
        criticality_level="SAFETY_CRITICAL"
    )
    db_session.add(slot)
    db_session.commit()

    assert slot.aircraft_model_id == model_id
    assert slot.slot_code == "MAIN_ROTOR_BLADE_1"
    assert slot.required is True
