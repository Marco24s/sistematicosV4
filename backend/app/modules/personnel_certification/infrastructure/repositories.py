from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.personnel_certification.domain.models import (
    CertificationRequirement,
    TaskAuthorization,
    TechnicalSpecialization,
    TechnicianCertification,
    TechnicianExperienceRecord,
    TechnicianProfile,
    CertificationAudit,
)
from app.shared.infrastructure.repositories import BaseRepository


class TechnicianProfileRepository(BaseRepository[TechnicianProfile]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicianProfile)

    def get_by_personnel_id(self, personnel_id: UUID) -> TechnicianProfile | None:
        statement = select(TechnicianProfile).where(
            TechnicianProfile.personnel_id == personnel_id,
            TechnicianProfile.is_deleted.is_(False),
        )
        return self.session.scalars(statement).first()


class TechnicalSpecializationRepository(BaseRepository[TechnicalSpecialization]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicalSpecialization)


class TechnicianCertificationRepository(BaseRepository[TechnicianCertification]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicianCertification)

    def list_active_by_profile_id(self, technician_profile_id: UUID) -> list[TechnicianCertification]:
        statement = select(TechnicianCertification).where(
            TechnicianCertification.technician_profile_id == technician_profile_id,
            TechnicianCertification.active.is_(True),
            TechnicianCertification.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class CertificationRequirementRepository(BaseRepository[CertificationRequirement]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CertificationRequirement)

    def list_by_task_type(self, task_type: str) -> list[CertificationRequirement]:
        statement = select(CertificationRequirement).where(
            CertificationRequirement.task_type == task_type,
            CertificationRequirement.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class TechnicianExperienceRecordRepository(BaseRepository[TechnicianExperienceRecord]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicianExperienceRecord)


class TaskAuthorizationRepository(BaseRepository[TaskAuthorization]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TaskAuthorization)


class CertificationAuditRepository(BaseRepository[CertificationAudit]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CertificationAudit)
