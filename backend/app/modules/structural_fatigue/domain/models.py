from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class StructuralFatigueRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "structural_fatigue_records"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False, index=True)
    accumulated_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    g_force_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    landing_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    corrosion_index: Mapped[float] = mapped_column(default=0.0, nullable=False)
    crack_detection_level: Mapped[float] = mapped_column(default=0.0, nullable=False)
    inspection_interval_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
