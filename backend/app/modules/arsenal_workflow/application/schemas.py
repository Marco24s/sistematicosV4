from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.arsenal_workflow.domain.models import (
    ComponentReceptionStatus,
    EngineeringReviewStatus,
    MaintenanceRequestPriority,
    MaintenanceRequestStatus,
    QualityInspectionStatus,
    RepairTaskStatus,
    SectionAssignmentStatus,
    ServiceReleaseStatus,
)


class MaintenanceRequestCreate(BaseModel):
    asset_id: UUID
    origin_department_id: UUID
    priority: MaintenanceRequestPriority
    failure_report_id: UUID
    requested_by: str


class MaintenanceRequestRead(MaintenanceRequestCreate):
    id: UUID
    status: MaintenanceRequestStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ComponentReceptionRead(BaseModel):
    id: UUID
    maintenance_request_id: UUID
    received_by_department_id: UUID
    received_at: datetime
    condition_notes: str | None
    documentation_complete: bool
    status: ComponentReceptionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SectionAssignmentRead(BaseModel):
    id: UUID
    maintenance_request_id: UUID
    assigned_section_id: UUID
    assigned_by: str
    assigned_at: datetime
    priority: MaintenanceRequestPriority
    status: SectionAssignmentStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class EngineeringReviewRead(BaseModel):
    id: UUID
    maintenance_request_id: UUID
    engineer_id: UUID
    analysis_date: datetime
    failure_analysis: str
    repairable: bool
    recommended_action: str
    status: EngineeringReviewStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class EngineeringInstructionRead(BaseModel):
    id: UUID
    engineering_review_id: UUID
    instruction_code: str
    procedure_description: str
    required_tools: str | None
    required_parts: str | None
    safety_notes: str | None
    issued_by: str
    issued_at: datetime
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class RepairTaskRead(BaseModel):
    id: UUID
    maintenance_request_id: UUID
    section_assignment_id: UUID
    assigned_technician_id: UUID
    engineering_instruction_id: UUID
    started_at: datetime | None
    completed_at: datetime | None
    repair_notes: str | None
    status: RepairTaskStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class QualityInspectionRead(BaseModel):
    id: UUID
    repair_task_id: UUID
    inspector_id: UUID
    inspection_date: datetime
    approved: bool
    inspection_notes: str | None
    certification_number: str | None
    status: QualityInspectionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceReleaseRead(BaseModel):
    id: UUID
    asset_id: UUID
    quality_inspection_id: UUID
    released_by: str
    release_date: datetime
    new_condition: str
    returned_to_department_id: UUID
    status: ServiceReleaseStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
