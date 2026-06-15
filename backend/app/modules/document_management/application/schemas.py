from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.document_management.domain.models import (
    AssetDocumentStatus,
    PreservationStatus,
    ServiceCardStatus,
    TechnicalHistoryActionType,
    WorkflowPackageStatus,
)


class DocumentTypeRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    mandatory: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AssetDocumentRead(BaseModel):
    id: UUID
    asset_id: UUID
    document_type_id: UUID
    document_code: str
    version: str
    issued_date: date
    expiration_date: date | None
    active: bool
    created_by: str
    status: AssetDocumentStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicalHistoryEntryRead(BaseModel):
    id: UUID
    asset_document_id: UUID
    entry_date: datetime
    action_type: TechnicalHistoryActionType
    performed_by: str
    notes: str | None
    current_hours: Decimal
    current_cycles: int
    condition_after_action: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceStatusCardRead(BaseModel):
    id: UUID
    asset_id: UUID
    current_status: ServiceCardStatus
    issued_date: date
    issued_by: str
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class PreservationRecordRead(BaseModel):
    id: UUID
    asset_id: UUID
    preservation_start: date
    preservation_interval_days: int
    next_preservation_check: date
    last_preservation_check: date | None
    status: PreservationStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class WorkflowDocumentPackageRead(BaseModel):
    id: UUID
    asset_id: UUID
    package_code: str
    created_by: str
    status: WorkflowPackageStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
