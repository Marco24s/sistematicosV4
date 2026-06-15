from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.maintenance.domain.models import (
    FailureSeverity,
    MaintenanceIntervalType,
    WorkOrderPriority,
    WorkOrderStatus,
)


class MaintenanceProgramCreate(BaseModel):
    name: str
    interval_type: MaintenanceIntervalType
    interval_value: int


class MaintenanceProgramRead(BaseModel):
    id: UUID
    name: str
    interval_type: MaintenanceIntervalType
    interval_value: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MaintenanceCounterCreate(BaseModel):
    asset_id: UUID
    maintenance_program_id: UUID
    current_usage: int = 0
    remaining_usage: int
    next_due: date | None = None


class MaintenanceCounterRead(BaseModel):
    id: UUID
    asset_id: UUID
    maintenance_program_id: UUID
    current_usage: int
    remaining_usage: int
    next_due: date | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class FailureReportCreate(BaseModel):
    asset_id: UUID
    reported_by: str
    failure_date: date
    description: str
    severity: FailureSeverity
    aircraft_id: UUID | None = None


class FailureReportRead(BaseModel):
    id: UUID
    asset_id: UUID
    reported_by: str
    failure_date: date
    description: str
    severity: FailureSeverity
    aircraft_id: UUID | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class WorkOrderCreate(BaseModel):
    failure_report_id: UUID
    origin_department_id: UUID
    assigned_department_id: UUID
    priority: WorkOrderPriority


class WorkOrderRead(BaseModel):
    id: UUID
    failure_report_id: UUID
    origin_department_id: UUID
    assigned_department_id: UUID
    priority: WorkOrderPriority
    status: WorkOrderStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
