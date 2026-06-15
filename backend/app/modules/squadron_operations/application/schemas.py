from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.squadron_operations.domain.models import (
    AircraftInspectionIntervalType,
    AircraftInspectionStatus,
    AirworthinessBlockSeverity,
    MaintenanceActionStatus,
    MountedComponentStatus,
    SquadronInventoryMovementType,
    SquadronQualityApprovalStatus,
    StatisticalControlStatus,
)


class AircraftConfigurationRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    configuration_name: str
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MountedComponentRead(BaseModel):
    id: UUID
    aircraft_configuration_id: UUID
    asset_id: UUID
    position_code: str
    installation_date: datetime
    installed_by: str
    status: MountedComponentStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AircraftInspectionProgramRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    inspection_name: str
    interval_type: AircraftInspectionIntervalType
    interval_value: int
    last_performed: date | None
    next_due: date | None
    status: AircraftInspectionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class StatisticalControlRecordRead(BaseModel):
    id: UUID
    asset_id: UUID
    current_hours: Decimal
    remaining_hours: Decimal | None
    current_cycles: int
    remaining_cycles: int | None
    calendar_expiration: date | None
    next_inspection_due: date | None
    status: StatisticalControlStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MaintenanceActionRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    performed_by: str
    action_type: str
    description: str
    performed_at: datetime
    requires_quality_approval: bool
    status: MaintenanceActionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SquadronQualityApprovalRead(BaseModel):
    id: UUID
    maintenance_action_id: UUID
    inspector_id: UUID
    approved: bool
    notes: str | None
    approved_at: datetime
    status: SquadronQualityApprovalStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SquadronInventoryMovementRead(BaseModel):
    id: UUID
    asset_id: UUID
    movement_type: SquadronInventoryMovementType
    origin_department_id: UUID | None
    destination_department_id: UUID | None
    performed_by: str
    movement_date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AirworthinessBlockRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    reason: str
    blocked_since: datetime
    severity: AirworthinessBlockSeverity
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
