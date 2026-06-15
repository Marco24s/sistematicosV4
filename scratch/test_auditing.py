import os
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.auditing.application.services import log_audit_event
from app.modules.auditing.domain.models import AuditEvent

db = SessionLocal()

try:
    event = log_audit_event(
        db=db,
        user_id=uuid.uuid4(),
        action="TEST_ACTION",
        entity_type="TestEntity",
        entity_id=uuid.uuid4(),
        origin_terminal="localhost",
        document_reference="DOC-TEST-001",
        old_state={"status": "DRAFT"},
        new_state={"status": "APPROVED"},
        reason="Testing the Military Audit Engine"
    )
    db.commit()
    print("Audit Event created successfully with ID:", event.id)
    
    # Query it back
    fetched = db.query(AuditEvent).filter_by(id=event.id).first()
    print("Fetched action:", fetched.action)
    print("Fetched new_state:", fetched.new_state)

except Exception as e:
    import traceback
    traceback.print_exc()
