from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin


class DisposalRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "disposal_requests"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False) # EXPIRED, CRACK_DETECTED, etc.
    initiated_by: Mapped[str] = mapped_column(String(180), nullable=False)
    engineering_review_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class DisposalApproval(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "disposal_approvals"

    disposal_request_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("disposal_requests.id"), nullable=False, index=True)
    approved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    approval_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
