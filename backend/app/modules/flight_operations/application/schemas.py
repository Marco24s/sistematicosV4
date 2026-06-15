from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.flight_operations.domain.models import (
    ConsumptionType,
    CrewRole,
    FlightSheetStatus,
    InstallationEventType,
    InstalledAssetStatus,
    MissionStatus,
    MissionType,
    OperationalAlertSeverity,
    OperationalAlertStatus,
)


class MissionCreate(BaseModel):
    organization_id: UUID
    mission_code: str
    mission_type: MissionType
    planned_flight_hours: Decimal
    status: MissionStatus = MissionStatus.PLANNED


class MissionRead(BaseModel):
    id: UUID
    organization_id: UUID
    mission_code: str
    mission_type: MissionType
    planned_flight_hours: Decimal
    status: MissionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class CrewAssignmentCreate(BaseModel):
    mission_id: UUID
    personnel_id: UUID
    role: CrewRole


class CrewAssignmentRead(BaseModel):
    id: UUID
    mission_id: UUID
    personnel_id: UUID
    role: CrewRole
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class FlightSheetCreate(BaseModel):
    mission_id: UUID
    aircraft_asset_id: UUID
    fuel_loaded: Decimal
    aircraft_weight: Decimal
    planned_departure_time: datetime
    actual_departure_time: datetime | None = None
    actual_arrival_time: datetime | None = None
    planned_hours: Decimal
    actual_hours_flown: Decimal | None = None
    technical_observations: str | None = None
    reported_failures: str | None = None
    status: FlightSheetStatus = FlightSheetStatus.PREPARED


class FlightSheetRead(BaseModel):
    id: UUID
    mission_id: UUID
    aircraft_asset_id: UUID
    fuel_loaded: Decimal
    aircraft_weight: Decimal
    planned_departure_time: datetime
    actual_departure_time: datetime | None
    actual_arrival_time: datetime | None
    planned_hours: Decimal
    actual_hours_flown: Decimal | None
    technical_observations: str | None
    reported_failures: str | None
    status: FlightSheetStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class InstalledAssetCreate(BaseModel):
    aircraft_asset_id: UUID
    installed_asset_id: UUID
    position_code: str
    installation_date: datetime
    installed_by: str
    status: InstalledAssetStatus = InstalledAssetStatus.INSTALLED


class InstalledAssetRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    installed_asset_id: UUID
    position_code: str
    installation_date: datetime
    installed_by: str
    status: InstalledAssetStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class InstallationEventCreate(BaseModel):
    aircraft_asset_id: UUID
    asset_id: UUID
    event_type: InstallationEventType
    performed_by: str
    date: datetime
    notes: str | None = None


class InstallationEventRead(BaseModel):
    id: UUID
    aircraft_asset_id: UUID
    asset_id: UUID
    event_type: InstallationEventType
    performed_by: str
    date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class FlightHourConsumptionEventRead(BaseModel):
    id: UUID
    flight_sheet_id: UUID
    asset_id: UUID
    consumption_type: ConsumptionType
    hours_consumed: Decimal
    cycles_consumed: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class OperationalAlertRead(BaseModel):
    id: UUID
    asset_id: UUID
    flight_sheet_id: UUID | None
    severity: OperationalAlertSeverity
    status: OperationalAlertStatus
    alert_code: str
    message: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
