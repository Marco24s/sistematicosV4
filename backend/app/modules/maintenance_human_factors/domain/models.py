from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class HumanFactorIncident(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_human_factor_incidents"

    technician_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("maintenance_task_executions.id"), nullable=False, index=True)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False) # INCORRECT_INSTALLATION, etc.
    severity_level: Mapped[str] = mapped_column(String(50), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    investigation_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    corrective_action_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
