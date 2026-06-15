from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CertificationLevel(StrEnum):
    LEVEL_A = "LEVEL_A"
    LEVEL_B = "LEVEL_B"
    LEVEL_C = "LEVEL_C"
    INSPECTOR = "INSPECTOR"


class CertificationMinimumLevel(StrEnum):
    LEVEL_A = "LEVEL_A"
    LEVEL_B = "LEVEL_B"
    LEVEL_C = "LEVEL_C"


class CertificationAuditEventType(StrEnum):
    CREATED = "CREATED"
    UPGRADED = "UPGRADED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    RENEWED = "RENEWED"


class TechnicianProfile(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_technician_profiles"

    personnel_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True, index=True)
    technical_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_level: Mapped[CertificationLevel] = mapped_column(
        Enum(CertificationLevel, name="personnel_certification_level"),
        nullable=False,
    )
    years_of_experience: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    certifications: Mapped[list["TechnicianCertification"]] = relationship(back_populates="technician_profile")
    experience_records: Mapped[list["TechnicianExperienceRecord"]] = relationship(back_populates="technician_profile")
    task_authorizations: Mapped[list["TaskAuthorization"]] = relationship(back_populates="technician_profile")
    certification_audits: Mapped[list["CertificationAudit"]] = relationship(back_populates="technician_profile")


class TechnicalSpecialization(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_technical_specializations"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    certifications: Mapped[list["TechnicianCertification"]] = relationship(back_populates="specialization")
    requirements: Mapped[list["CertificationRequirement"]] = relationship(back_populates="required_specialization")


class TechnicianCertification(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_technician_certifications"

    technician_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technician_profiles.id"),
        nullable=False,
        index=True,
    )
    specialization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technical_specializations.id"),
        nullable=False,
        index=True,
    )
    certification_level: Mapped[CertificationLevel] = mapped_column(
        Enum(CertificationLevel, name="personnel_technician_certification_level"),
        nullable=False,
    )
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_by: Mapped[str] = mapped_column(String(180), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    technician_profile: Mapped[TechnicianProfile] = relationship(back_populates="certifications")
    specialization: Mapped[TechnicalSpecialization] = relationship(back_populates="certifications")


class CertificationRequirement(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_certification_requirements"
    __table_args__ = (UniqueConstraint("task_type", "required_specialization_id", name="uq_certification_requirement_task_specialization"),)

    task_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    required_specialization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technical_specializations.id"),
        nullable=False,
        index=True,
    )
    minimum_level: Mapped[CertificationMinimumLevel] = mapped_column(
        Enum(CertificationMinimumLevel, name="personnel_certification_minimum_level"),
        nullable=False,
    )
    requires_inspector_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    required_specialization: Mapped[TechnicalSpecialization] = relationship(back_populates="requirements")


class TechnicianExperienceRecord(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_technician_experience_records"

    technician_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technician_profiles.id"),
        nullable=False,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    asset_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hours_worked: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    supervised_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    technician_profile: Mapped[TechnicianProfile] = relationship(back_populates="experience_records")
    asset: Mapped[Asset | None] = relationship()


class TaskAuthorization(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_task_authorizations"

    technician_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technician_profiles.id"),
        nullable=False,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    authorized: Mapped[bool] = mapped_column(Boolean, nullable=False)
    authorization_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    authorized_by: Mapped[str] = mapped_column(String(180), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    technician_profile: Mapped[TechnicianProfile] = relationship(back_populates="task_authorizations")
    asset: Mapped[Asset] = relationship()


class CertificationAudit(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "personnel_certification_audits"

    technician_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personnel_technician_profiles.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[CertificationAuditEventType] = mapped_column(
        Enum(CertificationAuditEventType, name="personnel_certification_audit_event_type"),
        nullable=False,
    )
    previous_level: Mapped[CertificationLevel | None] = mapped_column(
        Enum(CertificationLevel, name="personnel_certification_audit_previous_level"),
        nullable=True,
    )
    new_level: Mapped[CertificationLevel | None] = mapped_column(
        Enum(CertificationLevel, name="personnel_certification_audit_new_level"),
        nullable=True,
    )
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    technician_profile: Mapped[TechnicianProfile] = relationship(back_populates="certification_audits")
