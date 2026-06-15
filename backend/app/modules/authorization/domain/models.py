from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import UUIDPrimaryKeyMixin

# Tabla asociativa many-to-many para Role-Permission
role_permission_association = Table(
    "role_permission_association",
    Base.metadata,
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("organization_roles.id"), primary_key=True),
    Column("permission_id", PG_UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
)


class OrganizationRole(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "organization_roles"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permission_association,
        back_populates="roles"
    )


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[OrganizationRole]] = relationship(
        secondary=role_permission_association,
        back_populates="permissions"
    )


class SystemUser(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "system_users"

    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    assignments: Mapped[list["UserAssignment"]] = relationship(back_populates="user")


class UserAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_assignments"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("system_users.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organization_roles.id"), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[SystemUser] = relationship(back_populates="assignments")
    role: Mapped[OrganizationRole] = relationship()


class DigitalSignatureCertificate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "digital_signatures"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    certificate_serial: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SecurityAuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "security_audit_events"

    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True) # login_attempt, permission_denied, etc.
    action_attempted: Mapped[str] = mapped_column(String(240), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
