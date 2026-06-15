from sqlalchemy.orm import Session

from app.modules.arsenal_workflow.domain.models import (
    AuditEvent,
    ComponentReception,
    EngineeringInstruction,
    EngineeringReview,
    MaintenanceRequest,
    QualityInspection,
    RepairTask,
    SectionAssignment,
    ServiceRelease,
)
from app.shared.infrastructure.repositories import BaseRepository


class MaintenanceRequestRepository(BaseRepository[MaintenanceRequest]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MaintenanceRequest)


class ComponentReceptionRepository(BaseRepository[ComponentReception]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ComponentReception)


class SectionAssignmentRepository(BaseRepository[SectionAssignment]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, SectionAssignment)


class EngineeringReviewRepository(BaseRepository[EngineeringReview]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, EngineeringReview)


class EngineeringInstructionRepository(BaseRepository[EngineeringInstruction]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, EngineeringInstruction)


class RepairTaskRepository(BaseRepository[RepairTask]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, RepairTask)


class QualityInspectionRepository(BaseRepository[QualityInspection]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, QualityInspection)


class ServiceReleaseRepository(BaseRepository[ServiceRelease]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ServiceRelease)


class AuditEventRepository(BaseRepository[AuditEvent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AuditEvent)
