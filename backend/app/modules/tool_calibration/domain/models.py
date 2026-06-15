from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class Tool(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tools"

    tool_serial: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CalibrationCertificate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "calibration_certificates"

    tool_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False, index=True)
    calibration_date: Mapped[date] = mapped_column(Date, nullable=False)
    calibration_due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    certification_document_code: Mapped[str] = mapped_column(String(120), nullable=False)


class ToolAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tool_assignments"

    tool_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False, index=True)
    assigned_at: Mapped[date] = mapped_column(Date, nullable=False)


class ToolUsageRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tools_usage_records"

    tool_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False, index=True)
    technician_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    checked_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calibration_valid_at_usage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    damage_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

