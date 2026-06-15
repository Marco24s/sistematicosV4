from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.modules.organization.domain.models import Department
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class MaintenanceIntervalType(StrEnum):
    FLIGHT_HOURS = "FLIGHT_HOURS"
    CALENDAR_DAYS = "CALENDAR_DAYS"
    CYCLES = "CYCLES"


class FailureSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    FLIGHT_SAFETY = "FLIGHT_SAFETY"


class WorkOrderPriority(StrEnum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    AOG = "AOG"
    FLIGHT_SAFETY = "FLIGHT_SAFETY"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    MISSION_CRITICAL = "MISSION_CRITICAL"
    SAR_PRIORITY = "SAR_PRIORITY"
    COMBAT_PRIORITY = "COMBAT_PRIORITY"


class MaintenanceLevel(StrEnum):
    O_LEVEL = "O-Level"
    I_LEVEL = "I-Level"
    D_LEVEL = "D-Level"


class WorkOrderStatus(StrEnum):
    CREATED = "CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    UNDER_ENGINEERING_REVIEW = "UNDER_ENGINEERING_REVIEW"
    IN_REPAIR = "IN_REPAIR"
    WAITING_QUALITY = "WAITING_QUALITY"
    COMPLETED = "COMPLETED"



class MaintenanceProgram(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "maintenance_programs"
    __table_args__ = (UniqueConstraint("name", "interval_type", "interval_value", name="uq_maintenance_programs_rule"),)

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    interval_type: Mapped[MaintenanceIntervalType] = mapped_column(
        Enum(MaintenanceIntervalType, name="maintenance_interval_type"),
        nullable=False,
    )
    interval_value: Mapped[int] = mapped_column(Integer, nullable=False)

    counters: Mapped[list["MaintenanceCounter"]] = relationship(
        back_populates="maintenance_program",
        cascade="all, delete-orphan",
    )


class MaintenanceCounter(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "maintenance_counters"
    __table_args__ = (UniqueConstraint("asset_id", "maintenance_program_id", name="uq_counter_asset_program"),)

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    maintenance_program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("maintenance_programs.id"),
        nullable=False,
        index=True,
    )
    current_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remaining_usage: Mapped[int] = mapped_column(Integer, nullable=False)
    next_due: Mapped[date | None] = mapped_column(Date, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="maintenance_counters")
    maintenance_program: Mapped[MaintenanceProgram] = relationship(back_populates="counters")


class FailureReport(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "failure_reports"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    reported_by: Mapped[str] = mapped_column(String(180), nullable=False)
    failure_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[FailureSeverity] = mapped_column(Enum(FailureSeverity, name="failure_severity"), nullable=False)
    aircraft_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id"),
        nullable=True,
        index=True,
    )

    asset: Mapped[Asset] = relationship(
        back_populates="failure_reports",
        foreign_keys=[asset_id],
    )
    aircraft: Mapped[Asset | None] = relationship(
        back_populates="aircraft_failure_reports",
        foreign_keys=[aircraft_id],
    )
    work_orders: Mapped[list["WorkOrder"]] = relationship(
        back_populates="failure_report",
        cascade="all, delete-orphan",
    )


class WorkOrder(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "work_orders"

    failure_report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("failure_reports.id"),
        nullable=False,
        index=True,
    )
    origin_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    assigned_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    priority: Mapped[WorkOrderPriority] = mapped_column(Enum(WorkOrderPriority, name="work_order_priority"), nullable=False)
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, name="work_order_status"),
        default=WorkOrderStatus.CREATED,
        nullable=False,
    )
    priority_level: Mapped[str] = mapped_column(String(50), default="NORMAL", nullable=False)
    priority_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    maintenance_level: Mapped[MaintenanceLevel] = mapped_column(Enum(MaintenanceLevel, name="maintenance_level"), default=MaintenanceLevel.O_LEVEL, nullable=False)

    failure_report: Mapped[FailureReport] = relationship(back_populates="work_orders")
    origin_department: Mapped[Department] = relationship(
        foreign_keys=[origin_department_id],
    )
    assigned_department: Mapped[Department] = relationship(
        foreign_keys=[assigned_department_id],
    )


class DeferredDefect(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "deferred_defects"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    failure_report_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("failure_reports.id"), nullable=False, index=True)
    allowed_until_hours: Mapped[float | None] = mapped_column(Integer, nullable=True)
    allowed_until_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    restriction_level: Mapped[str] = mapped_column(String(120), nullable=False)
    repair_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    approved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)


class MaintenanceTaskExecution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_task_executions"

    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    technician_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    certification_level: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    digital_signature_hash: Mapped[str] = mapped_column(String(240), nullable=False)


class MaintenanceDualInspection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_dual_inspections"

    execution_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("maintenance_task_executions.id"), nullable=False, index=True)
    inspector_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    second_inspector_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)


