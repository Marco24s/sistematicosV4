from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.auditing.domain.models import AuditEvent

def log_audit_event(
    db: Session,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID,
    origin_terminal: str | None = None,
    document_reference: str | None = None,
    old_state: dict | None = None,
    new_state: dict | None = None,
    reason: str | None = None
) -> AuditEvent:
    """
    Registra un evento crítico en la Caja Negra (Motor de Auditoría).
    Debe ser invocado explícitamente desde los servicios de dominio u orquestadores.
    """
    event = AuditEvent(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        origin_terminal=origin_terminal,
        document_reference=document_reference,
        old_state=old_state,
        new_state=new_state,
        reason=reason
    )
    db.add(event)
    # Recomendamos flush para que esté disponible inmediatamente en el contexto, 
    # pero el commit lo hará el request handler superior.
    db.flush()
    return event
