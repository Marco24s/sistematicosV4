from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.authorization.domain.models import SecurityAuditEvent

router = APIRouter()

class CreateAuditEventRequest(BaseModel):
    user_id: UUID | None = None
    event_type: str
    action_attempted: str
    details: str

@router.get("/security/audit-events", tags=["security"])
def list_audit_events(db: Session = Depends(get_db)):
    events = db.query(SecurityAuditEvent).order_by(SecurityAuditEvent.timestamp.desc()).all()
    return [
        {
            "id": str(e.id),
            "user_id": str(e.user_id) if e.user_id else None,
            "event_type": e.event_type,
            "action_attempted": e.action_attempted,
            "details": e.details,
            "timestamp": str(e.timestamp)
        } for e in events
    ]

@router.post("/security/audit-events", tags=["security"])
def create_audit_event(request: CreateAuditEventRequest, db: Session = Depends(get_db)):
    event = SecurityAuditEvent(
        id=uuid4(),
        user_id=request.user_id,
        event_type=request.event_type,
        action_attempted=request.action_attempted,
        details=request.details,
        timestamp=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    
    return {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "timestamp": str(event.timestamp)
    }
