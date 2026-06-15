from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.arsenal_workflow.domain.models import AuditEvent, QualityInspection, RepairTask
from app.modules.personnel_certification.domain.models import (
    CertificationAudit,
    CertificationAuditEventType,
    CertificationLevel,
    CertificationMinimumLevel,
    CertificationRequirement,
    TaskAuthorization,
    TechnicalSpecialization,
    TechnicianCertification,
    TechnicianExperienceRecord,
    TechnicianProfile,
)
from app.modules.squadron_operations.domain.models import MaintenanceAction, SquadronQualityApproval
from app.shared.domain.exceptions import DomainError


LEVEL_RANK: dict[CertificationLevel, int] = {
    CertificationLevel.LEVEL_A: 1,
    CertificationLevel.LEVEL_B: 2,
    CertificationLevel.LEVEL_C: 3,
    CertificationLevel.INSPECTOR: 4,
}

MINIMUM_LEVEL_RANK: dict[CertificationMinimumLevel, int] = {
    CertificationMinimumLevel.LEVEL_A: 1,
    CertificationMinimumLevel.LEVEL_B: 2,
    CertificationMinimumLevel.LEVEL_C: 3,
}


@dataclass(frozen=True)
class AuditedResult:
    entity: object
    audit_event: AuditEvent


@dataclass(frozen=True)
class CertificationResult:
    certification: TechnicianCertification
    certification_audit: CertificationAudit
    audit_event: AuditEvent


class PersonnelCertificationService:
    def certify_technician(
        self,
        technician_profile: TechnicianProfile,
        specialization: TechnicalSpecialization,
        certification_level: CertificationLevel,
        issued_date: date,
        expiration_date: date,
        issued_by: str,
        actor_id: str,
    ) -> CertificationResult:
        if expiration_date <= issued_date:
            raise DomainError("Certification expiration date must be after issued date.")

        certification = TechnicianCertification(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            specialization_id=specialization.id,
            certification_level=certification_level,
            issued_date=issued_date,
            expiration_date=expiration_date,
            issued_by=issued_by,
            active=True,
        )
        audit = self._certification_audit(
            technician_profile,
            CertificationAuditEventType.CREATED,
            technician_profile.current_level,
            certification_level,
            issued_by,
            f"Certification granted for {specialization.name}.",
        )
        return CertificationResult(
            certification=certification,
            certification_audit=audit,
            audit_event=self._audit_event(
                certification,
                actor_id,
                "otorgo habilitacion tecnica",
                None,
                self._certification_state(certification),
            ),
        )

    def validate_task_authorization(
        self,
        technician_profile: TechnicianProfile,
        task_type: str,
        requirement: CertificationRequirement,
        certifications: list[TechnicianCertification],
        as_of: date | None = None,
    ) -> None:
        if not technician_profile.active:
            raise DomainError("Technician profile is inactive.")

        as_of = as_of or date.today()
        matching = [
            certification
            for certification in certifications
            if certification.technician_profile_id == technician_profile.id
            and certification.specialization_id == requirement.required_specialization_id
            and certification.active
            and not certification.is_deleted
        ]
        if not matching:
            raise DomainError(f"Technician has no active certification for task {task_type}.")

        valid = [
            certification
            for certification in matching
            if certification.expiration_date >= as_of
            and LEVEL_RANK[certification.certification_level] >= MINIMUM_LEVEL_RANK[requirement.minimum_level]
        ]
        if not valid:
            raise DomainError("Technician certification is expired or below required level.")

    def authorize_critical_task(
        self,
        technician_profile: TechnicianProfile,
        task_type: str,
        asset_id: UUID,
        authorized: bool,
        authorization_date: datetime,
        authorized_by: str,
        reason: str,
        actor_id: str,
    ) -> AuditedResult:
        authorization = TaskAuthorization(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            task_type=task_type,
            asset_id=asset_id,
            authorized=authorized,
            authorization_date=authorization_date,
            authorized_by=authorized_by,
            reason=reason,
        )
        return self._result(
            authorization,
            actor_id,
            "registro autorizacion previa de tarea critica",
            None,
            self._authorization_state(authorization),
        )

    def record_experience(
        self,
        technician_profile: TechnicianProfile,
        task_type: str,
        asset_id: UUID | None,
        performed_at: datetime,
        hours_worked: Decimal,
        supervised_by: UUID | None,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        if hours_worked <= 0:
            raise DomainError("Experience hours must be greater than zero.")
        record = TechnicianExperienceRecord(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            task_type=task_type,
            asset_id=asset_id,
            performed_at=performed_at,
            hours_worked=hours_worked,
            supervised_by=supervised_by,
            notes=notes,
        )
        technician_profile.years_of_experience += hours_worked / Decimal("2080")
        return self._result(
            record,
            actor_id,
            "registro experiencia tecnica",
            None,
            self._experience_state(record),
        )

    def promote_technician_level(
        self,
        technician_profile: TechnicianProfile,
        new_level: CertificationLevel,
        performed_by: str,
        event_date: datetime,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        previous_level = technician_profile.current_level
        if LEVEL_RANK[new_level] <= LEVEL_RANK[previous_level]:
            raise DomainError("New level must be higher than current technician level.")
        technician_profile.current_level = new_level
        audit = CertificationAudit(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            event_type=CertificationAuditEventType.UPGRADED,
            previous_level=previous_level,
            new_level=new_level,
            performed_by=performed_by,
            event_date=event_date,
            notes=notes,
        )
        return self._result(
            audit,
            actor_id,
            "promovio nivel tecnico",
            {"current_level": previous_level},
            {"current_level": new_level, "certification_audit": self._certification_audit_state(audit)},
        )

    def revoke_certification(
        self,
        technician_profile: TechnicianProfile,
        certification: TechnicianCertification,
        performed_by: str,
        event_date: datetime,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        if certification.technician_profile_id != technician_profile.id:
            raise DomainError("Certification does not belong to technician profile.")
        before_state = self._certification_state(certification)
        certification.active = False
        audit = CertificationAudit(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            event_type=CertificationAuditEventType.REVOKED,
            previous_level=certification.certification_level,
            new_level=None,
            performed_by=performed_by,
            event_date=event_date,
            notes=notes,
        )
        return self._result(
            audit,
            actor_id,
            "revoco habilitacion tecnica",
            before_state,
            {"certification": self._certification_state(certification), "certification_audit": self._certification_audit_state(audit)},
        )

    def validate_inspector_signature(
        self,
        technician_profile: TechnicianProfile,
        certifications: list[TechnicianCertification],
        as_of: date | None = None,
    ) -> None:
        if technician_profile.current_level != CertificationLevel.INSPECTOR:
            raise DomainError("Only INSPECTOR level personnel can certify critical tasks.")
        as_of = as_of or date.today()
        if not any(
            certification.technician_profile_id == technician_profile.id
            and certification.active
            and certification.certification_level == CertificationLevel.INSPECTOR
            and certification.expiration_date >= as_of
            for certification in certifications
        ):
            raise DomainError("Inspector signature requires an active non-expired INSPECTOR certification.")

    def enforce_repair_task_start(
        self,
        repair_task: RepairTask,
        technician_profile: TechnicianProfile,
        requirement: CertificationRequirement,
        certifications: list[TechnicianCertification],
    ) -> None:
        self.validate_task_authorization(
            technician_profile,
            task_type=str(repair_task.maintenance_request_id),
            requirement=requirement,
            certifications=certifications,
        )

    def enforce_maintenance_action_execution(
        self,
        maintenance_action: MaintenanceAction,
        technician_profile: TechnicianProfile,
        requirement: CertificationRequirement,
        certifications: list[TechnicianCertification],
    ) -> None:
        self.validate_task_authorization(
            technician_profile,
            task_type=maintenance_action.action_type,
            requirement=requirement,
            certifications=certifications,
        )

    def enforce_quality_inspection_approval(
        self,
        quality_inspection: QualityInspection,
        inspector_profile: TechnicianProfile,
        certifications: list[TechnicianCertification],
    ) -> None:
        if not quality_inspection.approved:
            return
        self.validate_inspector_signature(inspector_profile, certifications)

    def enforce_squadron_quality_approval(
        self,
        squadron_quality_approval: SquadronQualityApproval,
        inspector_profile: TechnicianProfile,
        certifications: list[TechnicianCertification],
    ) -> None:
        if not squadron_quality_approval.approved:
            return
        self.validate_inspector_signature(inspector_profile, certifications)

    def _certification_audit(
        self,
        technician_profile: TechnicianProfile,
        event_type: CertificationAuditEventType,
        previous_level: CertificationLevel | None,
        new_level: CertificationLevel | None,
        performed_by: str,
        notes: str | None,
    ) -> CertificationAudit:
        return CertificationAudit(
            id=uuid4(),
            technician_profile_id=technician_profile.id,
            event_type=event_type,
            previous_level=previous_level,
            new_level=new_level,
            performed_by=performed_by,
            event_date=datetime.now(timezone.utc),
            notes=notes,
        )

    def _result(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditedResult:
        return AuditedResult(
            entity=entity,
            audit_event=self._audit_event(entity, actor_id, action, before_state, after_state),
        )

    def _audit_event(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditEvent:
        return AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            entity_type=type(entity).__name__,
            entity_id=entity.id,
            timestamp=datetime.now(timezone.utc),
            before_state=before_state,
            after_state=after_state,
        )

    def _certification_state(self, certification: TechnicianCertification) -> dict:
        return {
            "id": str(certification.id),
            "technician_profile_id": str(certification.technician_profile_id),
            "specialization_id": str(certification.specialization_id),
            "certification_level": certification.certification_level,
            "expiration_date": certification.expiration_date.isoformat(),
            "active": certification.active,
        }

    def _authorization_state(self, authorization: TaskAuthorization) -> dict:
        return {
            "id": str(authorization.id),
            "technician_profile_id": str(authorization.technician_profile_id),
            "task_type": authorization.task_type,
            "asset_id": str(authorization.asset_id),
            "authorized": authorization.authorized,
        }

    def _experience_state(self, record: TechnicianExperienceRecord) -> dict:
        return {
            "id": str(record.id),
            "technician_profile_id": str(record.technician_profile_id),
            "task_type": record.task_type,
            "asset_id": str(record.asset_id) if record.asset_id else None,
            "hours_worked": str(record.hours_worked),
        }

    def _certification_audit_state(self, audit: CertificationAudit) -> dict:
        return {
            "id": str(audit.id),
            "technician_profile_id": str(audit.technician_profile_id),
            "event_type": audit.event_type,
            "previous_level": audit.previous_level,
            "new_level": audit.new_level,
        }
