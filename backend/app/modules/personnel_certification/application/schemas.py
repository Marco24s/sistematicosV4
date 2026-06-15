from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.personnel_certification.domain.models import (
    CertificationAuditEventType,
    CertificationLevel,
    CertificationMinimumLevel,
)


class TechnicianProfileRead(BaseModel):
    id: UUID
    personnel_id: UUID
    technical_code: str
    join_date: date
    current_level: CertificationLevel
    years_of_experience: Decimal
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicalSpecializationRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicianCertificationRead(BaseModel):
    id: UUID
    technician_profile_id: UUID
    specialization_id: UUID
    certification_level: CertificationLevel
    issued_date: date
    expiration_date: date
    issued_by: str
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class CertificationRequirementRead(BaseModel):
    id: UUID
    task_type: str
    required_specialization_id: UUID
    minimum_level: CertificationMinimumLevel
    requires_inspector_approval: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicianExperienceRecordRead(BaseModel):
    id: UUID
    technician_profile_id: UUID
    task_type: str
    asset_id: UUID | None
    performed_at: datetime
    hours_worked: Decimal
    supervised_by: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TaskAuthorizationRead(BaseModel):
    id: UUID
    technician_profile_id: UUID
    task_type: str
    asset_id: UUID
    authorized: bool
    authorization_date: datetime
    authorized_by: str
    reason: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class CertificationAuditRead(BaseModel):
    id: UUID
    technician_profile_id: UUID
    event_type: CertificationAuditEventType
    previous_level: CertificationLevel | None
    new_level: CertificationLevel | None
    performed_by: str
    event_date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
