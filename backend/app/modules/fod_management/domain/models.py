from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class FODInspection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "fod_inspections"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    inspection_location: Mapped[str] = mapped_column(String(120), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleared_for_operation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class FODIncident(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "fod_incidents"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    incident_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    foreign_object_type: Mapped[str] = mapped_column(String(120), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
