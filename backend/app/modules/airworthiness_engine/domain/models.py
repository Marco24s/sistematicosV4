from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class AirworthinessDecision(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "airworthiness_decisions"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    decision_status: Mapped[str] = mapped_column(String(50), nullable=False) # AIRWORTHY, RESTRICTED_AIRWORTHY, etc.
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(180), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
