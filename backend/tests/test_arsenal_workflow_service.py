from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

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
from app.modules.arsenal_workflow.domain.services import ArsenalWorkflowService
from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, TechnicalHistory
from app.modules.maintenance.domain.models import FailureReport, FailureSeverity
from app.shared.domain.exceptions import DomainError


def make_asset() -> Asset:
    return Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="PN-HYD-001",
        serial_number="SN-HYD-001",
        nomenclature="Hydraulic Servo",
        condition=AssetCondition.UNSERVICEABLE,
        current_status=AssetStatus.IN_STOCK,
    )


def make_failure_report(asset: Asset) -> FailureReport:
    return FailureReport(
        id=uuid4(),
        asset_id=asset.id,
        reported_by="Mantenimiento Escuadrilla",
        failure_date=date.today(),
        description="Perdida de presion hidraulica en prueba posterior al vuelo.",
        severity=FailureSeverity.HIGH,
        aircraft_id=uuid4(),
    )


def make_technical_history(asset: Asset) -> TechnicalHistory:
    return TechnicalHistory(
        id=uuid4(),
        asset_id=asset.id,
        opened_date=date.today(),
        current_total_hours=120,
        current_total_cycles=34,
    )


def test_full_arsenal_workflow_registers_audit_on_each_step() -> None:
    service = ArsenalWorkflowService()
    now = datetime.now(timezone.utc)
    asset = make_asset()
    failure_report = make_failure_report(asset)
    history = make_technical_history(asset)
    squadron_store_id = uuid4()
    arsenal_support_id = uuid4()
    hydraulics_id = uuid4()
    engineer_id = uuid4()
    technician_id = uuid4()
    inspector_id = uuid4()

    request_result = service.create_maintenance_request(
        asset=asset,
        failure_report=failure_report,
        origin_department_id=squadron_store_id,
        priority=MaintenanceRequestPriority.HIGH,
        requested_by="Pañol Aeronautico",
        actor_id="store-chief",
    )
    request = request_result.entity

    reception_result = service.receive_component_at_arsenal(
        maintenance_request=request,
        failure_report=failure_report,
        technical_history=history,
        received_by_department_id=arsenal_support_id,
        received_at=now,
        condition_notes="Componente recibido con historial, parte y pedido.",
        actor_id="arsenal-support",
    )
    reception = reception_result.entity

    assignment_result = service.assign_to_repair_section(
        maintenance_request=request,
        assigned_section_id=hydraulics_id,
        assigned_by="Apoyo Arsenal",
        assigned_at=now,
        priority=MaintenanceRequestPriority.HIGH,
        actor_id="support-chief",
    )
    assignment = assignment_result.entity

    review_result = service.create_engineering_review(
        maintenance_request=request,
        engineer_id=engineer_id,
        analysis_date=now,
        failure_analysis="Fuga interna por desgaste de sello principal.",
        repairable=True,
        recommended_action="Reemplazar sellos y ejecutar prueba de banco.",
        status=EngineeringReviewStatus.APPROVED,
        actor_id="engineering",
    )
    review = review_result.entity

    instruction_result = service.issue_engineering_instruction(
        engineering_review=review,
        instruction_code="ING-HYD-0001",
        procedure_description="Desarme controlado, reemplazo de sellos, torque y prueba hidraulica.",
        required_tools="Banco hidraulico, torquimetro calibrado",
        required_parts="Kit sellos HYD-001",
        safety_notes="Despresurizar circuito antes del desmontaje.",
        issued_by="Ingenieria Arsenal",
        issued_at=now,
        actor_id="engineering",
    )
    instruction = instruction_result.entity
    instruction.engineering_review = review

    repair_result = service.start_repair_task(
        maintenance_request=request,
        section_assignment=assignment,
        engineering_instruction=instruction,
        assigned_technician_id=technician_id,
        started_at=now,
        actor_id="hydraulics-section",
    )
    repair_task = repair_result.entity

    complete_result = service.complete_repair(
        repair_task=repair_task,
        maintenance_request=request,
        completed_at=now,
        repair_notes="Sellos reemplazados. Prueba de banco satisfactoria.",
        actor_id="hydraulics-section",
    )

    inspection_result = service.execute_quality_inspection(
        repair_task=repair_task,
        inspector_id=inspector_id,
        inspection_date=now,
        approved=True,
        inspection_notes="Procedimiento respetado y personal habilitado.",
        certification_number="QC-2026-001",
        actor_id="quality-inspector",
    )
    inspection = inspection_result.entity

    release_result = service.release_component_to_service(
        asset=asset,
        maintenance_request=request,
        quality_inspection=inspection,
        released_by="Calidad Arsenal",
        release_date=now,
        new_condition="SERVICEABLE",
        returned_to_department_id=squadron_store_id,
        status=ServiceReleaseStatus.SERVICEABLE,
        actor_id="quality-chief",
    )

    assert request.status == MaintenanceRequestStatus.COMPLETED
    assert reception.status == ComponentReceptionStatus.RECEIVED
    assert assignment.status == SectionAssignmentStatus.IN_PROGRESS
    assert review.status == EngineeringReviewStatus.APPROVED
    assert repair_task.status == RepairTaskStatus.COMPLETED
    assert inspection.status == QualityInspectionStatus.APPROVED
    assert release_result.entity.status == ServiceReleaseStatus.SERVICEABLE

    audit_events = [
        request_result.audit_event,
        reception_result.audit_event,
        assignment_result.audit_event,
        review_result.audit_event,
        instruction_result.audit_event,
        repair_result.audit_event,
        complete_result.audit_event,
        inspection_result.audit_event,
        release_result.audit_event,
    ]
    assert len(audit_events) == 9
    assert all(event.actor_id for event in audit_events)
    assert all(event.entity_id for event in audit_events)
    assert complete_result.audit_event.before_state["status"] == RepairTaskStatus.IN_PROGRESS


def test_receive_component_rejects_incomplete_documentation() -> None:
    service = ArsenalWorkflowService()
    asset = make_asset()
    failure_report = make_failure_report(asset)
    request = service.create_maintenance_request(
        asset=asset,
        failure_report=failure_report,
        origin_department_id=uuid4(),
        priority=MaintenanceRequestPriority.NORMAL,
        requested_by="Pañol Aeronautico",
        actor_id="store-chief",
    ).entity

    result = service.receive_component_at_arsenal(
        maintenance_request=request,
        failure_report=failure_report,
        technical_history=None,
        received_by_department_id=uuid4(),
        received_at=datetime.now(timezone.utc),
        condition_notes="Falta historial tecnico.",
        actor_id="arsenal-support",
    )

    assert result.entity.status == ComponentReceptionStatus.REJECTED
    assert result.entity.documentation_complete is False
    assert request.status == MaintenanceRequestStatus.REJECTED


def test_start_repair_task_requires_approved_engineering_instruction() -> None:
    service = ArsenalWorkflowService()
    asset = make_asset()
    failure_report = make_failure_report(asset)
    request = service.create_maintenance_request(
        asset=asset,
        failure_report=failure_report,
        origin_department_id=uuid4(),
        priority=MaintenanceRequestPriority.NORMAL,
        requested_by="Pañol Aeronautico",
        actor_id="store-chief",
    ).entity
    assignment = service.assign_to_repair_section(
        maintenance_request=request,
        assigned_section_id=uuid4(),
        assigned_by="Apoyo Arsenal",
        assigned_at=datetime.now(timezone.utc),
        priority=MaintenanceRequestPriority.NORMAL,
        actor_id="support-chief",
    ).entity
    review = service.create_engineering_review(
        maintenance_request=request,
        engineer_id=uuid4(),
        analysis_date=datetime.now(timezone.utc),
        failure_analysis="No repair procedure approved yet.",
        repairable=True,
        recommended_action="Continue review.",
        status=EngineeringReviewStatus.UNDER_REVIEW,
        actor_id="engineering",
    ).entity

    with pytest.raises(DomainError):
        service.issue_engineering_instruction(
            engineering_review=review,
            instruction_code="ING-PENDING",
            procedure_description="Procedure not approved.",
            required_tools=None,
            required_parts=None,
            safety_notes=None,
            issued_by="Ingenieria",
            issued_at=datetime.now(timezone.utc),
            actor_id="engineering",
        )

    review.status = EngineeringReviewStatus.APPROVED
    instruction = service.issue_engineering_instruction(
        engineering_review=review,
        instruction_code="ING-APPROVED",
        procedure_description="Approved procedure.",
        required_tools=None,
        required_parts=None,
        safety_notes=None,
        issued_by="Ingenieria",
        issued_at=datetime.now(timezone.utc),
        actor_id="engineering",
    ).entity
    instruction.active = False
    instruction.engineering_review = review

    with pytest.raises(DomainError):
        service.start_repair_task(
            maintenance_request=request,
            section_assignment=assignment,
            engineering_instruction=instruction,
            assigned_technician_id=uuid4(),
            started_at=datetime.now(timezone.utc),
            actor_id="hydraulics-section",
        )


def test_release_component_requires_approved_quality_inspection() -> None:
    service = ArsenalWorkflowService()
    asset = make_asset()
    failure_report = make_failure_report(asset)
    request = service.create_maintenance_request(
        asset=asset,
        failure_report=failure_report,
        origin_department_id=uuid4(),
        priority=MaintenanceRequestPriority.NORMAL,
        requested_by="Pañol Aeronautico",
        actor_id="store-chief",
    ).entity
    repair_task = service.start_repair_task

    class Inspection:
        id = uuid4()
        status = QualityInspectionStatus.REJECTED
        approved = False

    with pytest.raises(DomainError):
        service.release_component_to_service(
            asset=asset,
            maintenance_request=request,
            quality_inspection=Inspection(),
            released_by="Calidad Arsenal",
            release_date=datetime.now(timezone.utc),
            new_condition="SERVICEABLE",
            returned_to_department_id=uuid4(),
            status=ServiceReleaseStatus.SERVICEABLE,
            actor_id="quality-chief",
        )
