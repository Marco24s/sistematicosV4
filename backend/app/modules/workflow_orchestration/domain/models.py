from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowStatus(StrEnum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class RepairCycleState(StrEnum):
    FAILURE_DETECTED = "FAILURE_DETECTED"
    REQUEST_CREATED = "REQUEST_CREATED"
    REPAIR_ASSIGNED = "REPAIR_ASSIGNED"
    UNDER_REPAIR = "UNDER_REPAIR"
    QUALITY_PENDING = "QUALITY_PENDING"
    SERVICE_RELEASED = "SERVICE_RELEASED"
    STOCK_AVAILABLE = "STOCK_AVAILABLE"
    COMPLETED = "COMPLETED"


class WorkflowInstance(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workflow_instances"

    workflow_type: Mapped[str] = mapped_column(String(80), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    current_state: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflow_status"),
        default=WorkflowStatus.RUNNING,
        nullable=False
    )

    transition_logs: Mapped[list["WorkflowTransitionLog"]] = relationship(
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )


class WorkflowTransitionLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workflow_transition_logs"

    workflow_instance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_instances.id"),
        nullable=False,
        index=True
    )
    from_state: Mapped[str] = mapped_column(String(80), nullable=False)
    to_state: Mapped[str] = mapped_column(String(80), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    performed_by: Mapped[str | None] = mapped_column(String(180), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    workflow_instance: Mapped[WorkflowInstance] = relationship(back_populates="transition_logs")
