from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.modules.arsenal_workflow.domain.models import (
    AuditEvent,
    ComponentReception,
    ComponentReceptionStatus,
    EngineeringInstruction,
    EngineeringReview,
    EngineeringReviewStatus,
    MaintenanceRequest,
    MaintenanceRequestPriority,
    MaintenanceRequestStatus,
    QualityInspection,
    QualityInspectionStatus,
    RepairTask,
    RepairTaskStatus,
    SectionAssignment,
    SectionAssignmentStatus,
    ServiceRelease,
    ServiceReleaseStatus,
)
from app.modules.assets.domain.models import Asset, TechnicalHistory
from app.modules.maintenance.domain.models import FailureReport
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class AuditedResult:
    entity: object
    audit_event: AuditEvent


class ArsenalWorkflowService:
    def create_maintenance_request(
        self,
        asset: Asset,
        failure_report: FailureReport,
        has_failure_report_document: bool,
        origin_department_id: UUID,
        priority: MaintenanceRequestPriority,
        requested_by: str,
        actor_id: str,
    ) -> AuditedResult:
        if not has_failure_report_document:
            raise DomainError("OPERACIÓN DENEGADA: No se puede enviar un componente al Arsenal sin el documento 'Failure Report' asociado.")
            
        if failure_report.asset_id != asset.id:
            raise DomainError("Failure report must belong to the removed component.")

        request = MaintenanceRequest(
            id=uuid4(),
            asset_id=asset.id,
            origin_department_id=origin_department_id,
            priority=priority,
            failure_report_id=failure_report.id,
            requested_by=requested_by,
            status=MaintenanceRequestStatus.CREATED,
        )
        return self._result(
            request,
            actor_id,
            "creo pedido de trabajo de Arsenal",
            before_state=None,
            after_state=self._maintenance_request_state(request),
        )

    def receive_component_at_arsenal(
        self,
        maintenance_request: MaintenanceRequest,
        failure_report: FailureReport | None,
        technical_history: TechnicalHistory | None,
        has_maintenance_action_form: bool,
        received_by_department_id: UUID,
        received_at: datetime,
        condition_notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        if not failure_report:
            raise DomainError("OPERACIÓN DENEGADA: No se puede recibir en Arsenal sin un 'Failure Report'.")
        if not has_maintenance_action_form:
            raise DomainError("OPERACIÓN DENEGADA: No se puede recibir en Arsenal sin un 'Maintenance Action Form' asociado.")

        before_state = self._maintenance_request_state(maintenance_request)
        documentation_complete = (
            failure_report is not None
            and technical_history is not None
            and maintenance_request.id is not None
            and failure_report.id == maintenance_request.failure_report_id
            and technical_history.asset_id == maintenance_request.asset_id
            and has_maintenance_action_form
        )

        reception = ComponentReception(
            id=uuid4(),
            maintenance_request_id=maintenance_request.id,
            received_by_department_id=received_by_department_id,
            received_at=received_at,
            condition_notes=condition_notes,
            documentation_complete=documentation_complete,
            status=ComponentReceptionStatus.RECEIVED if documentation_complete else ComponentReceptionStatus.REJECTED,
        )

        if not documentation_complete:
            maintenance_request.status = MaintenanceRequestStatus.REJECTED
            return self._result(
                reception,
                actor_id,
                "rechazo recepcion por documentacion incompleta",
                before_state=before_state,
                after_state={
                    "reception": self._component_reception_state(reception),
                    "maintenance_request": self._maintenance_request_state(maintenance_request),
                },
            )

        maintenance_request.status = MaintenanceRequestStatus.RECEIVED_BY_ARSENAL
        return self._result(
            reception,
            actor_id,
            "recibio componente en Arsenal con documentacion completa",
            before_state=before_state,
            after_state={
                "reception": self._component_reception_state(reception),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
            },
        )

    def assign_to_repair_section(
        self,
        maintenance_request: MaintenanceRequest,
        assigned_section_id: UUID,
        assigned_by: str,
        assigned_at: datetime,
        priority: MaintenanceRequestPriority,
        actor_id: str,
    ) -> AuditedResult:
        before_state = self._maintenance_request_state(maintenance_request)
        assignment = SectionAssignment(
            id=uuid4(),
            maintenance_request_id=maintenance_request.id,
            assigned_section_id=assigned_section_id,
            assigned_by=assigned_by,
            assigned_at=assigned_at,
            priority=priority,
            status=SectionAssignmentStatus.ASSIGNED,
        )
        maintenance_request.status = MaintenanceRequestStatus.ASSIGNED_TO_SECTION
        return self._result(
            assignment,
            actor_id,
            "asigno componente a seccion reparadora",
            before_state=before_state,
            after_state={
                "section_assignment": self._section_assignment_state(assignment),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
            },
        )

    def create_engineering_review(
        self,
        maintenance_request: MaintenanceRequest,
        engineer_id: UUID,
        analysis_date: datetime,
        failure_analysis: str,
        repairable: bool,
        recommended_action: str,
        status: EngineeringReviewStatus,
        actor_id: str,
    ) -> AuditedResult:
        before_state = self._maintenance_request_state(maintenance_request)
        review = EngineeringReview(
            id=uuid4(),
            maintenance_request_id=maintenance_request.id,
            engineer_id=engineer_id,
            analysis_date=analysis_date,
            failure_analysis=failure_analysis,
            repairable=repairable,
            recommended_action=recommended_action,
            status=status,
        )
        maintenance_request.status = (
            MaintenanceRequestStatus.WAITING_REPAIR if status == EngineeringReviewStatus.APPROVED else MaintenanceRequestStatus.UNDER_ENGINEERING_REVIEW
        )
        return self._result(
            review,
            actor_id,
            "analizo falla en Ingenieria",
            before_state=before_state,
            after_state={
                "engineering_review": self._engineering_review_state(review),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
            },
        )

    def issue_engineering_instruction(
        self,
        engineering_review: EngineeringReview,
        instruction_code: str,
        procedure_description: str,
        required_tools: str | None,
        required_parts: str | None,
        safety_notes: str | None,
        issued_by: str,
        issued_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        if engineering_review.status != EngineeringReviewStatus.APPROVED:
            raise DomainError("Engineering instruction requires an approved engineering review.")

        instruction = EngineeringInstruction(
            id=uuid4(),
            engineering_review_id=engineering_review.id,
            instruction_code=instruction_code,
            procedure_description=procedure_description,
            required_tools=required_tools,
            required_parts=required_parts,
            safety_notes=safety_notes,
            issued_by=issued_by,
            issued_at=issued_at,
            active=True,
        )
        return self._result(
            instruction,
            actor_id,
            "emitio instruccion tecnica de Ingenieria",
            before_state=self._engineering_review_state(engineering_review),
            after_state=self._engineering_instruction_state(instruction),
        )

    def start_repair_task(
        self,
        maintenance_request: MaintenanceRequest,
        section_assignment: SectionAssignment,
        engineering_instruction: EngineeringInstruction,
        assigned_technician_id: UUID,
        started_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        review = engineering_instruction.engineering_review
        if not engineering_instruction.active or review is None or review.status != EngineeringReviewStatus.APPROVED:
            raise DomainError("RepairTask cannot start without an active instruction backed by an approved engineering review.")
        if section_assignment.status not in {SectionAssignmentStatus.ASSIGNED, SectionAssignmentStatus.IN_PROGRESS}:
            raise DomainError("Repair section must be assigned before repair can start.")

        before_state = {
            "maintenance_request": self._maintenance_request_state(maintenance_request),
            "section_assignment": self._section_assignment_state(section_assignment),
        }
        repair_task = RepairTask(
            id=uuid4(),
            maintenance_request_id=maintenance_request.id,
            section_assignment_id=section_assignment.id,
            assigned_technician_id=assigned_technician_id,
            engineering_instruction_id=engineering_instruction.id,
            started_at=started_at,
            status=RepairTaskStatus.IN_PROGRESS,
        )
        maintenance_request.status = MaintenanceRequestStatus.UNDER_REPAIR
        section_assignment.status = SectionAssignmentStatus.IN_PROGRESS
        return self._result(
            repair_task,
            actor_id,
            "inicio reparacion en seccion tecnica",
            before_state=before_state,
            after_state={
                "repair_task": self._repair_task_state(repair_task),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
                "section_assignment": self._section_assignment_state(section_assignment),
            },
        )

    def complete_repair(
        self,
        repair_task: RepairTask,
        maintenance_request: MaintenanceRequest,
        has_repair_completion_record: bool,
        has_engineering_instruction: bool,
        is_instruction_required: bool,
        completed_at: datetime,
        repair_notes: str,
        actor_id: str,
    ) -> AuditedResult:
        if not has_repair_completion_record:
            raise DomainError("OPERACIÓN DENEGADA: No se puede completar la reparación sin un 'Repair Completion Record'.")
        if is_instruction_required and not has_engineering_instruction:
            raise DomainError("OPERACIÓN DENEGADA: Esta reparación requiere una 'Engineering Instruction' activa.")
            
            
        if repair_task.status != RepairTaskStatus.IN_PROGRESS:
            raise DomainError("Only an in-progress repair task can be completed.")

        before_state = self._repair_task_state(repair_task)
        repair_task.status = RepairTaskStatus.COMPLETED
        repair_task.completed_at = completed_at
        repair_task.repair_notes = repair_notes
        maintenance_request.status = MaintenanceRequestStatus.WAITING_QUALITY
        return self._result(
            repair_task,
            actor_id,
            "completo reparacion fisica",
            before_state=before_state,
            after_state={
                "repair_task": self._repair_task_state(repair_task),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
            },
        )

    def execute_quality_inspection(
        self,
        repair_task: RepairTask,
        inspector_id: UUID,
        inspection_date: datetime,
        approved: bool,
        inspection_notes: str | None,
        certification_number: str | None,
        actor_id: str,
    ) -> AuditedResult:
        if repair_task.status != RepairTaskStatus.COMPLETED:
            raise DomainError("Quality inspection requires a completed repair task.")

        inspection = QualityInspection(
            id=uuid4(),
            repair_task_id=repair_task.id,
            inspector_id=inspector_id,
            inspection_date=inspection_date,
            approved=approved,
            inspection_notes=inspection_notes,
            certification_number=certification_number,
            status=QualityInspectionStatus.APPROVED if approved else QualityInspectionStatus.REJECTED,
        )
        return self._result(
            inspection,
            actor_id,
            "aprobo reparacion en Calidad" if approved else "rechazo reparacion en Calidad",
            before_state=self._repair_task_state(repair_task),
            after_state=self._quality_inspection_state(inspection),
        )

    def release_component_to_service(
        self,
        asset: Asset,
        maintenance_request: MaintenanceRequest,
        quality_inspection: QualityInspection,
        has_service_release_certificate: bool,
        has_historical_record_book: bool,
        released_by: str,
        release_date: datetime,
        new_condition: str,
        returned_to_department_id: UUID,
        status: ServiceReleaseStatus,
        actor_id: str,
    ) -> AuditedResult:
        if not has_service_release_certificate:
            raise DomainError("OPERACIÓN DENEGADA: No se puede emitir el Service Release sin el 'Service Release Certificate' asociado.")
        if not has_historical_record_book:
            raise DomainError("OPERACIÓN DENEGADA: No se puede liberar el componente sin la actualización del 'Historical Record Book'.")
            
        if quality_inspection.status != QualityInspectionStatus.APPROVED or not quality_inspection.approved:
            raise DomainError("Component can only be released after an approved quality inspection.")

        before_state = self._maintenance_request_state(maintenance_request)
        release = ServiceRelease(
            id=uuid4(),
            asset_id=asset.id,
            quality_inspection_id=quality_inspection.id,
            released_by=released_by,
            release_date=release_date,
            new_condition=new_condition,
            returned_to_department_id=returned_to_department_id,
            status=status,
        )
        maintenance_request.status = MaintenanceRequestStatus.COMPLETED if status != ServiceReleaseStatus.UNSERVICEABLE else MaintenanceRequestStatus.REJECTED
        return self._result(
            release,
            actor_id,
            "libero componente a condicion de servicio",
            before_state=before_state,
            after_state={
                "service_release": self._service_release_state(release),
                "maintenance_request": self._maintenance_request_state(maintenance_request),
            },
        )

    def _result(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditedResult:
        return AuditedResult(
            entity=entity,
            audit_event=AuditEvent(
                id=uuid4(),
                actor_id=actor_id,
                action=action,
                entity_type=type(entity).__name__,
                entity_id=entity.id,
                timestamp=datetime.now(timezone.utc),
                before_state=before_state,
                after_state=after_state,
            ),
        )

    def _maintenance_request_state(self, request: MaintenanceRequest) -> dict:
        return {
            "id": str(request.id),
            "asset_id": str(request.asset_id),
            "origin_department_id": str(request.origin_department_id),
            "priority": request.priority,
            "failure_report_id": str(request.failure_report_id),
            "requested_by": request.requested_by,
            "status": request.status,
        }

    def _component_reception_state(self, reception: ComponentReception) -> dict:
        return {
            "id": str(reception.id),
            "maintenance_request_id": str(reception.maintenance_request_id),
            "documentation_complete": reception.documentation_complete,
            "status": reception.status,
        }

    def _section_assignment_state(self, assignment: SectionAssignment) -> dict:
        return {
            "id": str(assignment.id),
            "maintenance_request_id": str(assignment.maintenance_request_id),
            "assigned_section_id": str(assignment.assigned_section_id),
            "priority": assignment.priority,
            "status": assignment.status,
        }

    def _engineering_review_state(self, review: EngineeringReview) -> dict:
        return {
            "id": str(review.id),
            "maintenance_request_id": str(review.maintenance_request_id),
            "engineer_id": str(review.engineer_id),
            "repairable": review.repairable,
            "status": review.status,
        }

    def _engineering_instruction_state(self, instruction: EngineeringInstruction) -> dict:
        return {
            "id": str(instruction.id),
            "engineering_review_id": str(instruction.engineering_review_id),
            "instruction_code": instruction.instruction_code,
            "active": instruction.active,
        }

    def _repair_task_state(self, repair_task: RepairTask) -> dict:
        return {
            "id": str(repair_task.id),
            "maintenance_request_id": str(repair_task.maintenance_request_id),
            "engineering_instruction_id": str(repair_task.engineering_instruction_id),
            "status": repair_task.status,
        }

    def _quality_inspection_state(self, inspection: QualityInspection) -> dict:
        return {
            "id": str(inspection.id),
            "repair_task_id": str(inspection.repair_task_id),
            "approved": inspection.approved,
            "certification_number": inspection.certification_number,
            "status": inspection.status,
        }

    def _service_release_state(self, release: ServiceRelease) -> dict:
        return {
            "id": str(release.id),
            "asset_id": str(release.asset_id),
            "quality_inspection_id": str(release.quality_inspection_id),
            "new_condition": release.new_condition,
            "status": release.status,
        }
