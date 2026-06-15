from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AircraftModel(Base):
    __tablename__ = "aircraft_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EngineModel(Base):
    __tablename__ = "engine_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ComponentType(Base):
    __tablename__ = "component_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    requires_certificate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    life_limit_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    life_limit_cycles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calendar_limit_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AircraftModelAllowedComponent(Base):
    __tablename__ = "aircraft_model_allowed_components"
    __table_args__ = (UniqueConstraint("aircraft_model_id", "component_type_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    aircraft_model_id: Mapped[int] = mapped_column(ForeignKey("aircraft_models.id"), nullable=False)
    component_type_id: Mapped[int] = mapped_column(ForeignKey("component_types.id"), nullable=False)

    aircraft_model: Mapped[AircraftModel] = relationship()
    component_type: Mapped[ComponentType] = relationship()
