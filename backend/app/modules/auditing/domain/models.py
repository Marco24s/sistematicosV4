from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, JSON, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    """
    Caja Negra: Inmutable log de auditoría militar operacional.
    """
    __tablename__ = "auditing_audit_events"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    origin_terminal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    document_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    old_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
