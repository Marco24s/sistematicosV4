from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.assets.domain.models import AssetCondition, AssetStatus, TransferStatus


class AssetTypeCreate(BaseModel):
    name: str
    category: str


class AssetTypeRead(BaseModel):
    id: UUID
    name: str
    category: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AssetCreate(BaseModel):
    asset_type_id: UUID
    part_number: str
    serial_number: str
    nomenclature: str
    condition: AssetCondition = AssetCondition.QUARANTINED
    current_status: AssetStatus = AssetStatus.IN_STOCK
    current_custodian_id: UUID | None = None


class AssetRead(BaseModel):
    id: UUID
    asset_type_id: UUID
    part_number: str
    serial_number: str
    nomenclature: str
    condition: AssetCondition
    current_status: AssetStatus
    current_custodian_id: UUID | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicalHistoryCreate(BaseModel):
    asset_id: UUID
    opened_date: date
    current_total_hours: int = 0
    current_total_cycles: int = 0
    calendar_expiration: date | None = None
    preservation_expiration: date | None = None
    notes: str | None = None


class TechnicalHistoryRead(BaseModel):
    id: UUID
    asset_id: UUID
    opened_date: date
    current_total_hours: int
    current_total_cycles: int
    calendar_expiration: date | None
    preservation_expiration: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AssetTransferCreate(BaseModel):
    asset_id: UUID
    origin_department_id: UUID
    destination_department_id: UUID
    transfer_date: date
    reason: str


class AssetTransferRead(BaseModel):
    id: UUID
    asset_id: UUID
    origin_department_id: UUID
    destination_department_id: UUID
    transfer_date: date
    reason: str
    status: TransferStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AirworthinessFindingRead(BaseModel):
    code: str
    message: str
    asset_id: UUID | None = None
    serial_number: str | None = None


class AirworthinessAssessmentRead(BaseModel):
    asset_id: UUID
    is_airworthy: bool
    findings: list[AirworthinessFindingRead]
