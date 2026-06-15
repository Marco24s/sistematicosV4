from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class FleetAvailabilityReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_fleet_availability"

    report_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    total_aircraft: Mapped[int] = mapped_column(Integer, nullable=False)
    available_aircraft: Mapped[int] = mapped_column(Integer, nullable=False)
    non_operational_aircraft: Mapped[int] = mapped_column(Integer, nullable=False)


class MTBFReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_mtbf"

    asset_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mean_time_between_failures_hours: Mapped[float] = mapped_column(nullable=False)


class MTTRReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_mttr"

    asset_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mean_time_to_repair_days: Mapped[float] = mapped_column(nullable=False)


class SectionRepairTimeReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_section_repair_times"

    section_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    average_repair_days: Mapped[float] = mapped_column(nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TechnicianPerformanceReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_technician_performance"

    technician_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    tasks_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    average_rating: Mapped[float] = mapped_column(nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CriticalStockReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_critical_stock"

    asset_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_required: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(50), nullable=False) # LOW, CRITICAL
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExpiringComponentReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reporting_expiring_components"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    nomenclature: Mapped[str] = mapped_column(String(240), nullable=False)
    remaining_hours: Mapped[float] = mapped_column(nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
