from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AssetDocumentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"
    CANCELED = "CANCELED"


class TechnicalHistoryActionType(StrEnum):
    PURCHASED = "PURCHASED"
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"
    INSPECTED = "INSPECTED"
    REPAIRED = "REPAIRED"
    TRANSFERRED = "TRANSFERRED"
    SCRAPPED = "SCRAPPED"


class ServiceCardStatus(StrEnum):
    SERVICEABLE = "SERVICEABLE"
    UNSERVICEABLE = "UNSERVICEABLE"
    IN_REPAIR = "IN_REPAIR"
    INSPECTION_REQUIRED = "INSPECTION_REQUIRED"
    LIMITED_SERVICE = "LIMITED_SERVICE"
    PRESERVED = "PRESERVED"


class PreservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    OVERDUE = "OVERDUE"


class WorkflowPackageStatus(StrEnum):
    CREATED = "CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"


class DocumentType(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_document_types"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    asset_documents: Mapped[list["AssetDocument"]] = relationship(back_populates="document_type")
    validation_rules: Mapped[list["DocumentValidationRule"]] = relationship(back_populates="required_document_type")


class AssetDocument(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_asset_documents"
    __table_args__ = (UniqueConstraint("asset_id", "document_code", "version", name="uq_asset_document_code_version"),)

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    document_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_management_document_types.id"),
        nullable=False,
        index=True,
    )
    document_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[AssetDocumentStatus] = mapped_column(
        Enum(AssetDocumentStatus, name="document_management_asset_document_status"),
        default=AssetDocumentStatus.ACTIVE,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship()
    document_type: Mapped[DocumentType] = relationship(back_populates="asset_documents")
    technical_history_entries: Mapped[list["TechnicalHistoryEntry"]] = relationship(back_populates="asset_document")
    package_links: Mapped[list["PackageDocumentLink"]] = relationship(back_populates="asset_document")


class TechnicalHistoryEntry(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_technical_history_entries"

    asset_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_management_asset_documents.id"),
        nullable=False,
        index=True,
    )
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action_type: Mapped[TechnicalHistoryActionType] = mapped_column(
        Enum(TechnicalHistoryActionType, name="document_management_technical_history_action_type"),
        nullable=False,
    )
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    current_cycles: Mapped[int] = mapped_column(default=0, nullable=False)
    condition_after_action: Mapped[str] = mapped_column(String(120), nullable=False)

    asset_document: Mapped[AssetDocument] = relationship(back_populates="technical_history_entries")


class ServiceStatusCard(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_service_status_cards"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    current_status: Mapped[ServiceCardStatus] = mapped_column(
        Enum(ServiceCardStatus, name="document_management_service_card_status"),
        nullable=False,
    )
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_by: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    asset: Mapped[Asset] = relationship()


class PreservationRecord(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_preservation_records"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    preservation_start: Mapped[date] = mapped_column(Date, nullable=False)
    preservation_interval_days: Mapped[int] = mapped_column(nullable=False)
    next_preservation_check: Mapped[date] = mapped_column(Date, nullable=False)
    last_preservation_check: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PreservationStatus] = mapped_column(
        Enum(PreservationStatus, name="document_management_preservation_status"),
        default=PreservationStatus.ACTIVE,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship()


class WorkflowDocumentPackage(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_workflow_packages"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    package_code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    created_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[WorkflowPackageStatus] = mapped_column(
        Enum(WorkflowPackageStatus, name="document_management_workflow_package_status"),
        default=WorkflowPackageStatus.CREATED,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship()
    document_links: Mapped[list["PackageDocumentLink"]] = relationship(
        back_populates="workflow_package",
        cascade="all, delete-orphan",
    )


class PackageDocumentLink(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_package_document_links"
    __table_args__ = (UniqueConstraint("workflow_package_id", "asset_document_id", name="uq_package_document_link"),)

    workflow_package_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_management_workflow_packages.id"),
        nullable=False,
        index=True,
    )
    asset_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_management_asset_documents.id"),
        nullable=False,
        index=True,
    )
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workflow_package: Mapped[WorkflowDocumentPackage] = relationship(back_populates="document_links")
    asset_document: Mapped[AssetDocument] = relationship(back_populates="package_links")


class DocumentValidationRule(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_validation_rules"
    __table_args__ = (UniqueConstraint("workflow_type", "required_document_type_id", name="uq_document_validation_rule"),)

    workflow_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    required_document_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_management_document_types.id"),
        nullable=False,
        index=True,
    )
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    required_document_type: Mapped[DocumentType] = relationship(back_populates="validation_rules")


class DocumentComplianceCheck(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_management_compliance_checks"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    workflow_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validated_by: Mapped[str] = mapped_column(String(180), nullable=False)
    compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship()


class PhysicalDocumentCustody(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_management_physical_custody"

    document_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_management_asset_documents.id"), nullable=False, index=True)
    current_department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    transferred_from_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    transferred_to_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    received_by: Mapped[str] = mapped_column(String(180), nullable=False)
    released_by: Mapped[str] = mapped_column(String(180), nullable=False)
    transfer_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

