from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship



from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class EngineAssembly(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_assemblies"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False, index=True)
    engine_model: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class EngineSubModule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_submodules"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), nullable=False, index=True)
    submodule_name: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class EngineInspectionProgram(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_inspection_programs"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), nullable=False, index=True)
    inspection_name: Mapped[str] = mapped_column(String(180), nullable=False)
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    last_performed_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    next_due_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class EngineCycleCounter(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_cycle_counters"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), unique=True, nullable=False, index=True)
    total_operating_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_start_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_ng_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_np_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class EngineTrendMonitoring(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_trend_monitoring"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    turbine_temperature_c: Mapped[float] = mapped_column(nullable=False)
    oil_pressure_psi: Mapped[float] = mapped_column(nullable=False)
    vibration_level: Mapped[float] = mapped_column(nullable=False)
    
    egt_c: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    torque_percent: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    n1_percent: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    n2_percent: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    fuel_flow_gph: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    oil_temperature_c: Mapped[float] = mapped_column(nullable=False, server_default='0.0')


class OilAnalysisRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_oil_analysis_records"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), nullable=False, index=True)
    sampled_at: Mapped[date] = mapped_column(Date, nullable=False)
    iron_ppm: Mapped[float] = mapped_column(nullable=False)
    copper_ppm: Mapped[float] = mapped_column(nullable=False)
    silicon_ppm: Mapped[float] = mapped_column(nullable=False)
    aluminum_ppm: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    chrome_ppm: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    nickel_ppm: Mapped[float] = mapped_column(nullable=False, server_default='0.0')
    contamination_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    verdict: Mapped[str] = mapped_column(String(50), nullable=False) # NORMAL, WARNING, CRITICAL


class HotSectionInspection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_hot_section_inspections"

    engine_assembly_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("engine_assemblies.id"), nullable=False, index=True)
    inspected_at_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    inspected_date: Mapped[date] = mapped_column(Date, nullable=False)
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    findings: Mapped[str] = mapped_column(Text, nullable=False)


class EngineInstallationHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "engine_installation_history"

    engine_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    aircraft_asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aircraft_hours_at_installation: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aircraft_hours_at_removal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    engine_hours_accumulated: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

