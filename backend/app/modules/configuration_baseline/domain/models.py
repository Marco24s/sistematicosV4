from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class AircraftBaselineConfiguration(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "configuration_baselines"

    aircraft_model_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    approved_configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    approved_by_engineering: Mapped[str] = mapped_column(String(180), nullable=False)
    revision_number: Mapped[str] = mapped_column(String(50), nullable=False)
    certification_date: Mapped[date] = mapped_column(Date, nullable=False)


class ConfigurationDeviation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "configuration_deviations"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    deviation_type: Mapped[str] = mapped_column(String(80), nullable=False) # TEMPORARY_MODIFICATION, etc.
    approved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
