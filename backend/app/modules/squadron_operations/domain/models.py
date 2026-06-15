from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.modules.organization.domain.models import Department
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class MountedComponentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


class AircraftInspectionIntervalType(StrEnum):
    FLIGHT_HOURS = "FLIGHT_HOURS"
    CALENDAR_DAYS = "CALENDAR_DAYS"


class AircraftInspectionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"


class StatisticalControlStatus(StrEnum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    OVERDUE = "OVERDUE"
    GROUNDING_REQUIRED = "GROUNDING_REQUIRED"


class MaintenanceActionStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    WAITING_QUALITY = "WAITING_QUALITY"


class SquadronQualityApprovalStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SquadronInventoryMovementType(StrEnum):
    RECEIVED_FROM_ARSENAL = "RECEIVED_FROM_ARSENAL"
    DELIVERED_FOR_INSTALLATION = "DELIVERED_FOR_INSTALLATION"
    RECEIVED_AFTER_REMOVAL = "RECEIVED_AFTER_REMOVAL"
    PREPARED_FOR_ARSENAL_TRANSFER = "PREPARED_FOR_ARSENAL_TRANSFER"


class AirworthinessBlockSeverity(StrEnum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    GROUNDING = "GROUNDING"


class AircraftConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_aircraft_configurations"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    configuration_name: Mapped[str] = mapped_column(String(180), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aircraft: Mapped[Asset] = relationship()
    mounted_components: Mapped[list["MountedComponent"]] = relationship(
        back_populates="aircraft_configuration",
        cascade="all, delete-orphan",
    )


class MountedComponent(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_mounted_components"

    aircraft_configuration_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("squadron_aircraft_configurations.id"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    position_code: Mapped[str] = mapped_column(String(80), nullable=False)
    installation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    installed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[MountedComponentStatus] = mapped_column(
        Enum(MountedComponentStatus, name="squadron_mounted_component_status"),
        default=MountedComponentStatus.ACTIVE,
        nullable=False,
    )

    aircraft_configuration: Mapped[AircraftConfiguration] = relationship(back_populates="mounted_components")
    asset: Mapped[Asset] = relationship()


class AircraftInspectionProgram(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_aircraft_inspection_programs"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    inspection_name: Mapped[str] = mapped_column(String(180), nullable=False)
    interval_type: Mapped[AircraftInspectionIntervalType] = mapped_column(
        Enum(AircraftInspectionIntervalType, name="squadron_aircraft_inspection_interval_type"),
        nullable=False,
    )
    interval_value: Mapped[int] = mapped_column(nullable=False)
    last_performed: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[AircraftInspectionStatus] = mapped_column(
        Enum(AircraftInspectionStatus, name="squadron_aircraft_inspection_status"),
        default=AircraftInspectionStatus.ACTIVE,
        nullable=False,
    )

    aircraft: Mapped[Asset] = relationship()


class StatisticalControlRecord(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_statistical_control_records"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, unique=True, index=True)
    current_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    remaining_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    current_cycles: Mapped[int] = mapped_column(default=0, nullable=False)
    remaining_cycles: Mapped[int | None] = mapped_column(nullable=True)
    calendar_expiration: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_inspection_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatisticalControlStatus] = mapped_column(
        Enum(StatisticalControlStatus, name="squadron_statistical_control_status"),
        default=StatisticalControlStatus.NORMAL,
        nullable=False,
    )

    asset: Mapped[Asset] = relationship()


class MaintenanceAction(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_maintenance_actions"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requires_quality_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[MaintenanceActionStatus] = mapped_column(
        Enum(MaintenanceActionStatus, name="squadron_maintenance_action_status"),
        default=MaintenanceActionStatus.PENDING,
        nullable=False,
    )

    aircraft: Mapped[Asset] = relationship()
    quality_approvals: Mapped[list["SquadronQualityApproval"]] = relationship(back_populates="maintenance_action")


class SquadronQualityApproval(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_quality_approvals"

    maintenance_action_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("squadron_maintenance_actions.id"),
        nullable=False,
        index=True,
    )
    inspector_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SquadronQualityApprovalStatus] = mapped_column(
        Enum(SquadronQualityApprovalStatus, name="squadron_quality_approval_status"),
        nullable=False,
    )

    maintenance_action: Mapped[MaintenanceAction] = relationship(back_populates="quality_approvals")


class SquadronInventoryMovement(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_inventory_movements"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    movement_type: Mapped[SquadronInventoryMovementType] = mapped_column(
        Enum(SquadronInventoryMovementType, name="squadron_inventory_movement_type"),
        nullable=False,
    )
    origin_department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    destination_department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    movement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship()
    origin_department: Mapped[Department | None] = relationship(foreign_keys=[origin_department_id])
    destination_department: Mapped[Department | None] = relationship(foreign_keys=[destination_department_id])


class AirworthinessBlock(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "squadron_airworthiness_blocks"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    blocked_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[AirworthinessBlockSeverity] = mapped_column(
        Enum(AirworthinessBlockSeverity, name="squadron_airworthiness_block_severity"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aircraft: Mapped[Asset] = relationship()


class MountedComponentHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "squadron_mounted_component_history"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    component_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    position_code: Mapped[str] = mapped_column(String(80), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    installed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    installed_at_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by: Mapped[str | None] = mapped_column(String(180), nullable=True)
    removed_at_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    hours_consumed_in_position: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)


class AircraftOperationalInterruption(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "squadron_aircraft_operational_interruptions"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    interruption_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)


class ConfigurationSlot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "squadron_configuration_slots"

    aircraft_model_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    slot_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    slot_name: Mapped[str] = mapped_column(String(120), nullable=False)
    compatible_asset_types: Mapped[str] = mapped_column(Text, nullable=False) # CSV/JSON compatible ids
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criticality_level: Mapped[str] = mapped_column(String(50), nullable=False)


class AircraftConfigurationSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "squadron_aircraft_configuration_snapshots"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    flight_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    installed_components_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), nullable=False)


