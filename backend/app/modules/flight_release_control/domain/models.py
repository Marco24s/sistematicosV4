from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class FlightReleaseAuthorization(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "flight_release_authorizations"

    aircraft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    authorized_by: Mapped[str] = mapped_column(String(180), nullable=False)
    authorization_type: Mapped[str] = mapped_column(String(80), nullable=False) # NORMAL_RELEASE, RESTRICTED_RELEASE, COMBAT_RELEASE, etc.
    authorized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
