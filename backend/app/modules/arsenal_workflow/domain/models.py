from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.modules.maintenance.domain.models import FailureReport, MaintenanceLevel
from app.modules.organization.domain.models import Department
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class MaintenanceRequestStatus(StrEnum):
    CREATED = "CREATED"
    READY_FOR_TRANSFER = "READY_FOR_TRANSFER"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED_BY_ARSENAL = "RECEIVED_BY_ARSENAL"
    ASSIGNED_TO_SECTION = "ASSIGNED_TO_SECTION"
    UNDER_ENGINEERING_REVIEW = "UNDER_ENGINEERING_REVIEW"
    WAITING_REPAIR = "WAITING_REPAIR"
    UNDER_REPAIR = "UNDER_REPAIR"
    WAITING_QUALITY = "WAITING_QUALITY"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class MaintenanceRequestPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class ComponentReceptionStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"


class SectionAssignmentStatus(StrEnum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class EngineeringReviewStatus(StrEnum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RepairTaskStatus(StrEnum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QualityInspectionStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ServiceReleaseStatus(StrEnum):
    SERVICEABLE = "SERVICEABLE"
    LIMITED_SERVICE = "LIMITED_SERVICE"
    UNSERVICEABLE = "UNSERVICEABLE"


class MaintenanceRequest(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_maintenance_requests"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    origin_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    priority: Mapped[MaintenanceRequestPriority] = mapped_column(
        Enum(MaintenanceRequestPriority, name="arsenal_maintenance_request_priority"),
        nullable=False,
    )
    failure_report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("failure_reports.id"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[MaintenanceRequestStatus] = mapped_column(
        Enum(MaintenanceRequestStatus, name="arsenal_maintenance_request_status"),
        default=MaintenanceRequestStatus.CREATED,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship()
    origin_department: Mapped[Department] = relationship()
    failure_report: Mapped[FailureReport] = relationship()
    receptions: Mapped[list["ComponentReception"]] = relationship(back_populates="maintenance_request")
    section_assignments: Mapped[list["SectionAssignment"]] = relationship(back_populates="maintenance_request")
    engineering_reviews: Mapped[list["EngineeringReview"]] = relationship(back_populates="maintenance_request")
    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="maintenance_request")


class ComponentReception(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_component_receptions"

    maintenance_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_maintenance_requests.id"),
        nullable=False,
        index=True,
    )
    received_by_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    documentation_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ComponentReceptionStatus] = mapped_column(
        Enum(ComponentReceptionStatus, name="arsenal_component_reception_status"),
        default=ComponentReceptionStatus.PENDING_REVIEW,
        nullable=False,
    )
    
    failure_report_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    maintenance_action_form_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    work_order_code: Mapped[str | None] = mapped_column(String(120), nullable=True)

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="receptions")
    received_by_department: Mapped[Department] = relationship()


class SectionAssignment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_section_assignments"

    maintenance_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_maintenance_requests.id"),
        nullable=False,
        index=True,
    )
    assigned_section_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    assigned_by: Mapped[str] = mapped_column(String(180), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[MaintenanceRequestPriority] = mapped_column(
        Enum(MaintenanceRequestPriority, name="arsenal_section_assignment_priority"),
        nullable=False,
    )
    status: Mapped[SectionAssignmentStatus] = mapped_column(
        Enum(SectionAssignmentStatus, name="arsenal_section_assignment_status"),
        default=SectionAssignmentStatus.PENDING,
        nullable=False,
    )

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="section_assignments")
    assigned_section: Mapped[Department] = relationship()
    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="section_assignment")


class EngineeringReview(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_engineering_reviews"

    maintenance_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_maintenance_requests.id"),
        nullable=False,
        index=True,
    )
    engineer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    analysis_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    failure_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    repairable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EngineeringReviewStatus] = mapped_column(
        Enum(EngineeringReviewStatus, name="arsenal_engineering_review_status"),
        default=EngineeringReviewStatus.PENDING,
        nullable=False,
    )

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="engineering_reviews")
    instructions: Mapped[list["EngineeringInstruction"]] = relationship(back_populates="engineering_review")


class EngineeringInstruction(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_engineering_instructions"

    engineering_review_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_engineering_reviews.id"),
        nullable=False,
        index=True,
    )
    instruction_code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    procedure_description: Mapped[str] = mapped_column(Text, nullable=False)
    required_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_parts: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_by: Mapped[str] = mapped_column(String(180), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    engineering_review: Mapped[EngineeringReview] = relationship(back_populates="instructions")
    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="engineering_instruction")


class RepairTask(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_repair_tasks"

    maintenance_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_maintenance_requests.id"),
        nullable=False,
        index=True,
    )
    section_assignment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_section_assignments.id"),
        nullable=False,
        index=True,
    )
    assigned_technician_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    engineering_instruction_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_engineering_instructions.id"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repair_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RepairTaskStatus] = mapped_column(
        Enum(RepairTaskStatus, name="arsenal_repair_task_status"),
        default=RepairTaskStatus.WAITING,
        nullable=False,
    )
    maintenance_level: Mapped[MaintenanceLevel] = mapped_column(
        Enum(MaintenanceLevel, name="repair_maintenance_level"),
        default=MaintenanceLevel.I_LEVEL,
        nullable=False,
    )

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="repair_tasks")
    section_assignment: Mapped[SectionAssignment] = relationship(back_populates="repair_tasks")
    engineering_instruction: Mapped[EngineeringInstruction] = relationship(back_populates="repair_tasks")
    quality_inspections: Mapped[list["QualityInspection"]] = relationship(back_populates="repair_task")


class QualityInspection(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_quality_inspections"

    repair_task_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_repair_tasks.id"),
        nullable=False,
        index=True,
    )
    inspector_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    inspection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    inspection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    certification_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[QualityInspectionStatus] = mapped_column(
        Enum(QualityInspectionStatus, name="arsenal_quality_inspection_status"),
        default=QualityInspectionStatus.PENDING,
        nullable=False,
    )

    repair_task: Mapped[RepairTask] = relationship(back_populates="quality_inspections")
    service_releases: Mapped[list["ServiceRelease"]] = relationship(back_populates="quality_inspection")


class ServiceRelease(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "arsenal_service_releases"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    quality_inspection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("arsenal_quality_inspections.id"),
        nullable=False,
        index=True,
    )
    released_by: Mapped[str] = mapped_column(String(180), nullable=False)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_condition: Mapped[str] = mapped_column(String(120), nullable=False)
    returned_to_department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    status: Mapped[ServiceReleaseStatus] = mapped_column(
        Enum(ServiceReleaseStatus, name="arsenal_service_release_status"),
        nullable=False,
    )
    service_release_certificate_code: Mapped[str] = mapped_column(String(120), nullable=False, default="SRC-PENDING")
    historical_record_book_code: Mapped[str] = mapped_column(String(120), nullable=False, default="HRB-PENDING")

    asset: Mapped[Asset] = relationship()
    quality_inspection: Mapped[QualityInspection] = relationship(back_populates="service_releases")
    returned_to_department: Mapped[Department] = relationship()


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"

    actor_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(240), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ExternalRepairVendor(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "arsenal_external_repair_vendors"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ExternalRepairOrder(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "arsenal_external_repair_orders"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    vendor_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("arsenal_external_repair_vendors.id"), nullable=False, index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SENT_EXTERNAL", nullable=False)

