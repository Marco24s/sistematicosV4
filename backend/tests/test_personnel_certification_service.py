from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.arsenal_workflow.domain.models import QualityInspection, QualityInspectionStatus, RepairTask, RepairTaskStatus
from app.modules.personnel_certification.domain.models import (
    CertificationAuditEventType,
    CertificationLevel,
    CertificationMinimumLevel,
    CertificationRequirement,
    TechnicalSpecialization,
    TechnicianCertification,
    TechnicianProfile,
)
from app.modules.personnel_certification.domain.services import PersonnelCertificationService
from app.modules.squadron_operations.domain.models import (
    MaintenanceAction,
    MaintenanceActionStatus,
    SquadronQualityApproval,
    SquadronQualityApprovalStatus,
)
from app.shared.domain.exceptions import DomainError


def make_profile(level: CertificationLevel = CertificationLevel.LEVEL_A) -> TechnicianProfile:
    return TechnicianProfile(
        id=uuid4(),
        personnel_id=uuid4(),
        technical_code="TECH-001",
        join_date=date.today() - timedelta(days=1000),
        current_level=level,
        years_of_experience=Decimal("2.00"),
        active=True,
    )


def make_specialization(name: str = "HYDRAULIC_SYSTEMS") -> TechnicalSpecialization:
    return TechnicalSpecialization(id=uuid4(), name=name, description="Hydraulic systems certification.")


def make_requirement(specialization: TechnicalSpecialization, minimum=CertificationMinimumLevel.LEVEL_B) -> CertificationRequirement:
    return CertificationRequirement(
        id=uuid4(),
        task_type="REPAIR_HYDRAULIC_SERVO",
        required_specialization_id=specialization.id,
        minimum_level=minimum,
        requires_inspector_approval=True,
    )


def make_certification(
    profile: TechnicianProfile,
    specialization: TechnicalSpecialization,
    level: CertificationLevel = CertificationLevel.LEVEL_B,
    active: bool = True,
    expires_in_days: int = 30,
) -> TechnicianCertification:
    return TechnicianCertification(
        id=uuid4(),
        technician_profile_id=profile.id,
        specialization_id=specialization.id,
        certification_level=level,
        issued_date=date.today() - timedelta(days=100),
        expiration_date=date.today() + timedelta(days=expires_in_days),
        issued_by="Calidad",
        active=active,
    )


def test_certify_technician_creates_certification_and_audit() -> None:
    profile = make_profile()
    specialization = make_specialization()

    result = PersonnelCertificationService().certify_technician(
        technician_profile=profile,
        specialization=specialization,
        certification_level=CertificationLevel.LEVEL_B,
        issued_date=date.today(),
        expiration_date=date.today() + timedelta(days=365),
        issued_by="quality-chief",
        actor_id="quality-chief",
    )

    assert result.certification.certification_level == CertificationLevel.LEVEL_B
    assert result.certification_audit.event_type == CertificationAuditEventType.CREATED
    assert result.audit_event.entity_type == "TechnicianCertification"


def test_validate_task_authorization_accepts_active_matching_certification() -> None:
    profile = make_profile(CertificationLevel.LEVEL_B)
    specialization = make_specialization()
    requirement = make_requirement(specialization)
    certification = make_certification(profile, specialization)

    PersonnelCertificationService().validate_task_authorization(
        technician_profile=profile,
        task_type=requirement.task_type,
        requirement=requirement,
        certifications=[certification],
    )


def test_validate_task_authorization_rejects_expired_or_low_level() -> None:
    profile = make_profile(CertificationLevel.LEVEL_A)
    specialization = make_specialization()
    requirement = make_requirement(specialization, CertificationMinimumLevel.LEVEL_C)
    low_level = make_certification(profile, specialization, CertificationLevel.LEVEL_A)
    expired = make_certification(profile, specialization, CertificationLevel.LEVEL_C, expires_in_days=-1)

    with pytest.raises(DomainError):
        PersonnelCertificationService().validate_task_authorization(profile, requirement.task_type, requirement, [low_level])

    with pytest.raises(DomainError):
        PersonnelCertificationService().validate_task_authorization(profile, requirement.task_type, requirement, [expired])


def test_authorize_critical_task_and_record_experience_are_audited() -> None:
    service = PersonnelCertificationService()
    profile = make_profile()
    asset_id = uuid4()

    authorization = service.authorize_critical_task(
        technician_profile=profile,
        task_type="REPAIR_HYDRAULIC_SERVO",
        asset_id=asset_id,
        authorized=True,
        authorization_date=datetime.now(timezone.utc),
        authorized_by="quality-chief",
        reason="Technician certified and assigned by maintenance chief.",
        actor_id="quality-chief",
    )
    experience = service.record_experience(
        technician_profile=profile,
        task_type="REPAIR_HYDRAULIC_SERVO",
        asset_id=asset_id,
        performed_at=datetime.now(timezone.utc),
        hours_worked=Decimal("4.00"),
        supervised_by=uuid4(),
        notes="Hydraulic servo bench repair.",
        actor_id="maintenance-chief",
    )

    assert authorization.entity.authorized is True
    assert experience.entity.hours_worked == Decimal("4.00")
    assert profile.years_of_experience > Decimal("2.00")
    assert authorization.audit_event.entity_type == "TaskAuthorization"
    assert experience.audit_event.entity_type == "TechnicianExperienceRecord"


def test_promote_and_revoke_certification_create_audit_records() -> None:
    service = PersonnelCertificationService()
    profile = make_profile(CertificationLevel.LEVEL_A)
    specialization = make_specialization()
    certification = make_certification(profile, specialization, CertificationLevel.LEVEL_B)

    promotion = service.promote_technician_level(
        technician_profile=profile,
        new_level=CertificationLevel.LEVEL_B,
        performed_by="quality-chief",
        event_date=datetime.now(timezone.utc),
        notes="Experience and exams completed.",
        actor_id="quality-chief",
    )
    revocation = service.revoke_certification(
        technician_profile=profile,
        certification=certification,
        performed_by="quality-chief",
        event_date=datetime.now(timezone.utc),
        notes="Certification suspended by quality.",
        actor_id="quality-chief",
    )

    assert profile.current_level == CertificationLevel.LEVEL_B
    assert promotion.entity.event_type == CertificationAuditEventType.UPGRADED
    assert revocation.entity.event_type == CertificationAuditEventType.REVOKED
    assert certification.active is False


def test_validate_inspector_signature_requires_inspector_certification() -> None:
    inspector = make_profile(CertificationLevel.INSPECTOR)
    specialization = make_specialization("AIRFRAME")
    certification = make_certification(inspector, specialization, CertificationLevel.INSPECTOR)

    PersonnelCertificationService().validate_inspector_signature(inspector, [certification])

    non_inspector = make_profile(CertificationLevel.LEVEL_C)
    with pytest.raises(DomainError):
        PersonnelCertificationService().validate_inspector_signature(non_inspector, [certification])


def test_enforcement_blocks_existing_workflow_without_certification_or_inspector() -> None:
    service = PersonnelCertificationService()
    profile = make_profile(CertificationLevel.LEVEL_A)
    specialization = make_specialization()
    requirement = make_requirement(specialization, CertificationMinimumLevel.LEVEL_B)
    repair_task = RepairTask(
        id=uuid4(),
        maintenance_request_id=uuid4(),
        section_assignment_id=uuid4(),
        assigned_technician_id=profile.id,
        engineering_instruction_id=uuid4(),
        status=RepairTaskStatus.WAITING,
    )
    maintenance_action = MaintenanceAction(
        id=uuid4(),
        aircraft_asset_id=uuid4(),
        performed_by="tech",
        action_type=requirement.task_type,
        description="Hydraulic action",
        performed_at=datetime.now(timezone.utc),
        requires_quality_approval=True,
        status=MaintenanceActionStatus.WAITING_QUALITY,
    )
    quality_inspection = QualityInspection(
        id=uuid4(),
        repair_task_id=repair_task.id,
        inspector_id=profile.id,
        inspection_date=datetime.now(timezone.utc),
        approved=True,
        status=QualityInspectionStatus.APPROVED,
    )
    squadron_approval = SquadronQualityApproval(
        id=uuid4(),
        maintenance_action_id=maintenance_action.id,
        inspector_id=profile.id,
        approved=True,
        approved_at=datetime.now(timezone.utc),
        status=SquadronQualityApprovalStatus.APPROVED,
    )

    with pytest.raises(DomainError):
        service.enforce_repair_task_start(repair_task, profile, requirement, [])
    with pytest.raises(DomainError):
        service.enforce_maintenance_action_execution(maintenance_action, profile, requirement, [])
    with pytest.raises(DomainError):
        service.enforce_quality_inspection_approval(quality_inspection, profile, [])
    with pytest.raises(DomainError):
        service.enforce_squadron_quality_approval(squadron_approval, profile, [])
