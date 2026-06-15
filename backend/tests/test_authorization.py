from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.shared.domain.exceptions import DomainError
from app.shared.events.bus import event_bus

# Modelos del modulo de seguridad
from app.modules.authorization.domain.models import (
    OrganizationRole,
    Permission,
    UserAssignment,
    DigitalSignatureCertificate,
    SecurityAuditEvent
)
from app.modules.authorization.domain.policies import AuthorizationPolicy


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    yield session
    session.close()


def test_permission_denied_logs_violation(db_session: Session) -> None:
    policy = AuthorizationPolicy()
    user_id = uuid4()
    org_id = uuid4()
    
    # 1. Ejecutar acción de crear misión sin permisos
    with pytest.raises(DomainError) as exc_info:
        policy.can_create_mission(user_id, org_id, db_session)
    
    assert "Unauthorized to create mission" in str(exc_info.value)

    # 2. Verificar que se grabó la violación en SecurityAuditEvent
    from sqlalchemy import select
    stmt = select(SecurityAuditEvent).where(SecurityAuditEvent.user_id == user_id)
    event = db_session.scalars(stmt).first()

    assert event is not None
    assert event.event_type == "PERMISSION_DENIED"
    assert event.action_attempted == "CREATE_MISSION"


def test_authorized_quality_approval_with_valid_signature(db_session: Session) -> None:
    policy = AuthorizationPolicy()
    user_id = uuid4()
    org_id = uuid4()
    dept_id = uuid4()
    
    # 1. Crear el permiso de calidad
    perm = Permission(id=uuid4(), name="APPROVE_QUALITY_INSPECTION")
    db_session.add(perm)
    
    # 2. Crear rol de inspector y enlazar permiso
    role = OrganizationRole(id=uuid4(), name="QUALITY_INSPECTOR", permissions=[perm])
    db_session.add(role)
    db_session.commit()
    
    # 3. Crear asignación de usuario
    assignment = UserAssignment(
        user_id=user_id,
        organization_id=org_id,
        department_id=dept_id,
        role_id=role.id,
        active=True
    )
    db_session.add(assignment)

    # 4. Crear firma digital activa
    signature = DigitalSignatureCertificate(
        user_id=user_id,
        certificate_serial="CERT-SIG-9981",
        issued_at=datetime.utcnow() - timedelta(days=10),
        expires_at=datetime.utcnow() + timedelta(days=365),
        active=True
    )
    db_session.add(signature)
    db_session.commit()

    # 5. Evaluar política
    assert policy.can_approve_quality(user_id, "CERT-SIG-9981", db_session) is True


def test_expired_signature_raises_error(db_session: Session) -> None:
    policy = AuthorizationPolicy()
    user_id = uuid4()
    org_id = uuid4()
    dept_id = uuid4()

    # 1. Crear el permiso de calidad
    perm = Permission(id=uuid4(), name="APPROVE_QUALITY_INSPECTION")
    db_session.add(perm)
    
    # 2. Crear rol de inspector y asignar
    role = OrganizationRole(id=uuid4(), name="QUALITY_INSPECTOR", permissions=[perm])
    db_session.add(role)
    
    assignment = UserAssignment(
        user_id=user_id,
        organization_id=org_id,
        department_id=dept_id,
        role_id=role.id,
        active=True
    )
    db_session.add(assignment)

    # 3. Registrar firma digital expirada
    signature = DigitalSignatureCertificate(
        user_id=user_id,
        certificate_serial="CERT-SIG-EXPIRED",
        issued_at=datetime.utcnow() - timedelta(days=200),
        expires_at=datetime.utcnow() - timedelta(days=20),
        active=True
    )

    db_session.add(signature)
    db_session.commit()

    # 4. Intentar aprobar con firma vencida
    with pytest.raises(DomainError) as exc_info:
        policy.can_approve_quality(user_id, "CERT-SIG-EXPIRED", db_session)

    assert "certificate has expired" in str(exc_info.value)
