from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationType(StrEnum):
    SQUADRON = "SQUADRON"
    ARSENAL = "ARSENAL"


class DepartmentType(StrEnum):
    OPERATIONS = "OPERATIONS"
    LOGISTICS = "LOGISTICS"
    MAINTENANCE = "MAINTENANCE"
    QUALITY = "QUALITY"
    STATISTICS = "STATISTICS"
    AERONAUTICAL_STORES = "AERONAUTICAL_STORES"
    PROCUREMENT = "PROCUREMENT"
    ENGINEERING = "ENGINEERING"
    SUPPORT = "SUPPORT"
    ACCESSORIES = "ACCESSORIES"
    HYDRAULICS = "HYDRAULICS"
    ENGINES = "ENGINES"
    DYNAMIC_COMPONENTS = "DYNAMIC_COMPONENTS"
    ELECTRICAL_ACCESSORIES = "ELECTRICAL_ACCESSORIES"


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    organization_type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="organization_type"),
        nullable=False,
    )

    departments: Mapped[list["Department"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class Department(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_departments_organization_name"),)

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    department_type: Mapped[DepartmentType] = mapped_column(
        Enum(DepartmentType, name="department_type"),
        nullable=False,
    )

    organization: Mapped[Organization] = relationship(back_populates="departments")
    custody_assets: Mapped[list["Asset"]] = relationship(  # type: ignore[name-defined]
        back_populates="current_custodian",
        foreign_keys="Asset.current_custodian_id",
    )
    outgoing_transfers: Mapped[list["AssetTransfer"]] = relationship(  # type: ignore[name-defined]
        back_populates="origin_department",
        foreign_keys="AssetTransfer.origin_department_id",
    )
    incoming_transfers: Mapped[list["AssetTransfer"]] = relationship(  # type: ignore[name-defined]
        back_populates="destination_department",
        foreign_keys="AssetTransfer.destination_department_id",
    )
