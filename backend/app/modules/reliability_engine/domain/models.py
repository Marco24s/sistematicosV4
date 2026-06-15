from uuid import UUID

from sqlalchemy import ForeignKey, String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class ReliabilityTrend(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reliability_trends"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), unique=True, nullable=False, index=True)
    mtbf: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mttr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    repeated_failures_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_rate_per_100_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
