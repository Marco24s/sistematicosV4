from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.modules.organization.domain.models import Organization
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class MissionStatus(StrEnum):
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class MissionType(StrEnum):
    TRAINING = "TRAINING"
    TRANSPORT = "TRANSPORT"
    SEARCH_AND_RESCUE = "SEARCH_AND_RESCUE"
    PATROL = "PATROL"
    TEST_FLIGHT = "TEST_FLIGHT"


class CrewRole(StrEnum):
    PILOT = "PILOT"
    COPILOT = "COPILOT"
    FLIGHT_ENGINEER = "FLIGHT_ENGINEER"
    CREW_CHIEF = "CREW_CHIEF"
    OBSERVER = "OBSERVER"


class FlightSheetStatus(StrEnum):
    PREPARED = "PREPARED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    CLOSED = "CLOSED"


class InstalledAssetStatus(StrEnum):
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"


class InstallationEventType(StrEnum):
    INSTALL = "INSTALL"
    REMOVE = "REMOVE"


class ConsumptionType(StrEnum):
    FLIGHT_HOURS = "FLIGHT_HOURS"
    CYCLES = "CYCLES"


class OperationalAlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class OperationalAlertStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLOSED = "CLOSED"


class Mission(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "missions"
    __table_args__ = (UniqueConstraint("organization_id", "mission_code", name="uq_missions_organization_code"),)

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    mission_code: Mapped[str] = mapped_column(String(80), nullable=False)
    mission_type: Mapped[MissionType] = mapped_column(Enum(MissionType, name="mission_type"), nullable=False)
    planned_flight_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[MissionStatus] = mapped_column(
        Enum(MissionStatus, name="mission_status"),
        default=MissionStatus.PLANNED,
        nullable=False,
    )

    organization: Mapped[Organization] = relationship()
    crew_assignments: Mapped[list["CrewAssignment"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )
    flight_sheet: Mapped["FlightSheet | None"] = relationship(
        back_populates="mission",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CrewAssignment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "crew_assignments"
    __table_args__ = (UniqueConstraint("mission_id", "personnel_id", "role", name="uq_crew_assignment_role"),)

    mission_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False, index=True)
    personnel_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[CrewRole] = mapped_column(Enum(CrewRole, name="crew_role"), nullable=False)

    mission: Mapped[Mission] = relationship(back_populates="crew_assignments")


class FlightSheet(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "flight_sheets"

    mission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("missions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    fuel_loaded: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aircraft_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    planned_departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    actual_hours_flown: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    technical_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_failures: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[FlightSheetStatus] = mapped_column(
        Enum(FlightSheetStatus, name="flight_sheet_status"),
        default=FlightSheetStatus.PREPARED,
        nullable=False,
    )

    mission: Mapped[Mission] = relationship(back_populates="flight_sheet")
    aircraft: Mapped[Asset] = relationship(foreign_keys=[aircraft_asset_id])
    consumption_events: Mapped[list["FlightHourConsumptionEvent"]] = relationship(
        back_populates="flight_sheet",
        cascade="all, delete-orphan",
    )


class InstalledAsset(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "installed_assets"
    __table_args__ = (
        UniqueConstraint("aircraft_asset_id", "installed_asset_id", "status", name="uq_installed_asset_status"),
    )

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    installed_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    position_code: Mapped[str] = mapped_column(String(80), nullable=False)
    installation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    installed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[InstalledAssetStatus] = mapped_column(
        Enum(InstalledAssetStatus, name="installed_asset_status"),
        default=InstalledAssetStatus.INSTALLED,
        nullable=False,
    )

    aircraft: Mapped[Asset] = relationship(foreign_keys=[aircraft_asset_id])
    installed_asset: Mapped[Asset] = relationship(foreign_keys=[installed_asset_id])


class InstallationEvent(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "installation_events"

    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    event_type: Mapped[InstallationEventType] = mapped_column(
        Enum(InstallationEventType, name="installation_event_type"),
        nullable=False,
    )
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    aircraft: Mapped[Asset] = relationship(foreign_keys=[aircraft_asset_id])
    asset: Mapped[Asset] = relationship(foreign_keys=[asset_id])


class FlightHourConsumptionEvent(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "flight_hour_consumption_events"

    flight_sheet_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("flight_sheets.id"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    consumption_type: Mapped[ConsumptionType] = mapped_column(Enum(ConsumptionType, name="consumption_type"), nullable=False)
    hours_consumed: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, nullable=False)
    cycles_consumed: Mapped[int] = mapped_column(default=0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    flight_sheet: Mapped[FlightSheet] = relationship(back_populates="consumption_events")
    asset: Mapped[Asset] = relationship()


class OperationalAlert(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "operational_alerts"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    flight_sheet_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("flight_sheets.id"), nullable=True, index=True)
    severity: Mapped[OperationalAlertSeverity] = mapped_column(
        Enum(OperationalAlertSeverity, name="operational_alert_severity"),
        nullable=False,
    )
    status: Mapped[OperationalAlertStatus] = mapped_column(
        Enum(OperationalAlertStatus, name="operational_alert_status"),
        default=OperationalAlertStatus.OPEN,
        nullable=False,
    )
    alert_code: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    asset: Mapped[Asset] = relationship()
    flight_sheet: Mapped[FlightSheet | None] = relationship()
