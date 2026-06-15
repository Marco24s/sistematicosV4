from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.shared.domain.events import DomainEvent
from app.modules.authorization.domain.models import SecurityAuditEvent

def handle_security_violation(event: DomainEvent, session: Session) -> None:
    # Registrar incidentes de denegación de permisos de forma asíncrona / desacoplada
    payload = event.payload
    audit = SecurityAuditEvent(
        user_id=UUID(payload["user_id"]) if payload.get("user_id") else None,
        event_type="UNAUTHORIZED_VIOLATION",
        action_attempted=payload.get("action", "UNKNOWN"),
        details=payload.get("reason", "Violación detectada por el motor de integración"),
        timestamp=datetime.now(timezone.utc)
    )
    session.add(audit)
    session.flush()
