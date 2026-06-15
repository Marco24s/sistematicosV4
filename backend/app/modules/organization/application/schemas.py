from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.organization.domain.models import DepartmentType, OrganizationType


class OrganizationCreate(BaseModel):
    name: str
    organization_type: OrganizationType


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    organization_type: OrganizationType
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    organization_id: UUID
    name: str
    department_type: DepartmentType


class DepartmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    department_type: DepartmentType
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
