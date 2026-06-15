from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.modules.organization.domain.models import Department
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AssetCondition(StrEnum):
    SERVICEABLE = "SERVICEABLE"
    UNSERVICEABLE = "UNSERVICEABLE"
    REPAIRABLE = "REPAIRABLE"
    QUARANTINED = "QUARANTINED"
    PRESERVED = "PRESERVED"
    CONDEMNED = "CONDEMNED"


class AssetStatus(StrEnum):
    PENDING_COMMISSIONING = "PENDING_COMMISSIONING"
    UNDER_INSPECTION = "UNDER_INSPECTION"
    ACTIVE_SERVICE = "ACTIVE_SERVICE"
    QUARANTINED = "QUARANTINED"
    STORAGE = "STORAGE"
    IN_STOCK = "IN_STOCK"
    INSTALLED = "INSTALLED"
    IN_TRANSFER = "IN_TRANSFER"
    IN_REPAIR = "IN_REPAIR"
    WAITING_QUALITY = "WAITING_QUALITY"
    RELEASED = "RELEASED"
    GROUNDED = "GROUNDED"
    SCRAPPED = "SCRAPPED"


class TransferStatus(StrEnum):
    CREATED = "CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class AssetClassification(StrEnum):
    REPAIRABLE = "REPAIRABLE"
    CONSUMABLE = "CONSUMABLE"
    ROTABLE = "ROTABLE"
    CALIBRATION_CONTROLLED = "CALIBRATION_CONTROLLED"
    LIFE_LIMITED = "LIFE_LIMITED"
    DISPOSABLE = "DISPOSABLE"

class AirworthinessStatus(StrEnum):
    AIRWORTHY = "AIRWORTHY"
    NON_AIRWORTHY = "NON_AIRWORTHY"
    RESTRICTED = "RESTRICTED"
    AWAITING_CERTIFICATION = "AWAITING_CERTIFICATION"
    UNKNOWN = "UNKNOWN"


class AssetType(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "asset_types"
    __table_args__ = (UniqueConstraint("name", "category", name="uq_asset_types_name_category"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    assets: Mapped[list["Asset"]] = relationship(back_populates="asset_type")


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "assets"

    asset_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    part_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    nomenclature: Mapped[str] = mapped_column(String(240), nullable=False)
    condition: Mapped[AssetCondition] = mapped_column(
        Enum(AssetCondition, name="asset_condition"),
        default=AssetCondition.QUARANTINED,
        nullable=False,
    )
    current_status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status"),
        default=AssetStatus.IN_STOCK,
        nullable=False,
    )
    current_custodian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
    )
    classification: Mapped[AssetClassification] = mapped_column(
        Enum(AssetClassification, name="asset_classification"),
        default=AssetClassification.REPAIRABLE,
        nullable=False
    )
    interchangeability_group: Mapped[str | None] = mapped_column(String(120), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    manufacturer_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    compatible_platforms: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # New Global Engine Fields
    organization_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    current_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    airworthiness_status: Mapped[AirworthinessStatus] = mapped_column(
        Enum(AirworthinessStatus, name="airworthiness_status"),
        default=AirworthinessStatus.UNKNOWN,
        nullable=False,
    )

    asset_type: Mapped[AssetType] = relationship(back_populates="assets")
    current_custodian: Mapped[Department | None] = relationship(
        back_populates="custody_assets",
        foreign_keys=[current_custodian_id],
    )
    organization_owner: Mapped["Organization | None"] = relationship(
        "Organization",
        foreign_keys=[organization_owner_id],
    )
    technical_history: Mapped["TechnicalHistory | None"] = relationship(
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["AssetDocument"]] = relationship(  # type: ignore[name-defined]
        back_populates="asset",
        cascade="all, delete-orphan",
        foreign_keys="AssetDocument.asset_id"
    )

    transfers: Mapped[list["AssetTransfer"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    maintenance_counters: Mapped[list["MaintenanceCounter"]] = relationship(  # type: ignore[name-defined]
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    failure_reports: Mapped[list["FailureReport"]] = relationship(  # type: ignore[name-defined]
        back_populates="asset",
        foreign_keys="FailureReport.asset_id",
    )
    aircraft_failure_reports: Mapped[list["FailureReport"]] = relationship(  # type: ignore[name-defined]
        back_populates="aircraft",
        foreign_keys="FailureReport.aircraft_id",
    )


class TechnicalHistory(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "technical_histories"

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    opened_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_total_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_total_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calendar_expiration: Mapped[date | None] = mapped_column(Date, nullable=True)
    preservation_expiration: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="technical_history")


class AssetTransfer(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "asset_transfers"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    origin_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    destination_department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, name="transfer_status"),
        default=TransferStatus.CREATED,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship(back_populates="transfers")
    origin_department: Mapped[Department] = relationship(
        back_populates="outgoing_transfers",
        foreign_keys=[origin_department_id],
    )
    destination_department: Mapped[Department] = relationship(
        back_populates="incoming_transfers",
        foreign_keys=[destination_department_id],
    )


class AssetConfigurationNode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_configuration_nodes"

    parent_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    child_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False, index=True)
    position_code: Mapped[str] = mapped_column(String(80), nullable=False)
    installation_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    installed_at: Mapped[date] = mapped_column(Date, nullable=False)


class AssetLifecycleEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_lifecycle_events"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actor: Mapped[str] = mapped_column(String(180), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class LifeLimitedComponent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "assets_life_limited_components"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False, index=True)
    life_limit_hours: Mapped[float] = mapped_column(nullable=False)
    life_limit_cycles: Mapped[int] = mapped_column(nullable=False)
    consumed_hours: Mapped[float] = mapped_column(default=0.0, nullable=False)
    consumed_cycles: Mapped[int] = mapped_column(default=0, nullable=False)
    remaining_hours: Mapped[float] = mapped_column(nullable=False)
    remaining_cycles: Mapped[int] = mapped_column(nullable=False)


