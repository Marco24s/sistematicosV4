from datetime import datetime
from uuid import UUID

from app.modules.assets.domain.models import Asset, AssetStatus
from app.modules.maintenance.domain.models import (
    FailureReport,
    MaintenanceCounter,
    MaintenanceProgram,
    WorkOrder,
    WorkOrderStatus,
)
from app.shared.domain.exceptions import DomainError


class MaintenanceCounterService:
    def initialize_counter(self, asset_id: UUID, program: MaintenanceProgram, current_usage: int = 0) -> MaintenanceCounter:
        remaining_usage = program.interval_value - current_usage
        return MaintenanceCounter(
            asset_id=asset_id,
            maintenance_program_id=program.id,
            current_usage=current_usage,
            remaining_usage=remaining_usage,
        )


class FailureReportService:
    def register_failure(self, asset: Asset, failure_report: FailureReport) -> FailureReport:
        if failure_report.asset_id != asset.id:
            raise DomainError("Failure report asset_id must match the failed asset.")
        asset.current_status = AssetStatus.GROUNDED
        return failure_report


class WorkOrderService:
    def create_from_failure_report(self, failure_report: FailureReport, work_order: WorkOrder, has_failure_report_document: bool) -> WorkOrder:
        if not has_failure_report_document:
            raise DomainError("OPERACIÓN DENEGADA: No se puede abrir una Work Order sin el documento 'Failure Report' asociado.")
            
        if work_order.failure_report_id != failure_report.id:
            raise DomainError("Work order must reference its source failure report.")
        work_order.status = WorkOrderStatus.CREATED
        return work_order

    def transition(
        self, 
        work_order: WorkOrder, 
        next_status: WorkOrderStatus,
        has_work_order_document: bool = False,
        has_maintenance_action_form: bool = False
    ) -> WorkOrder:
        allowed = {
            WorkOrderStatus.CREATED: {WorkOrderStatus.IN_TRANSIT},
            WorkOrderStatus.IN_TRANSIT: {WorkOrderStatus.RECEIVED},
            WorkOrderStatus.RECEIVED: {WorkOrderStatus.UNDER_ENGINEERING_REVIEW, WorkOrderStatus.IN_REPAIR},
            WorkOrderStatus.UNDER_ENGINEERING_REVIEW: {WorkOrderStatus.IN_REPAIR},
            WorkOrderStatus.IN_REPAIR: {WorkOrderStatus.WAITING_QUALITY},
            WorkOrderStatus.WAITING_QUALITY: {WorkOrderStatus.COMPLETED},
            WorkOrderStatus.COMPLETED: set(),
        }
        if next_status not in allowed[work_order.status]:
            raise DomainError(f"Invalid work order transition {work_order.status} -> {next_status}.")
            
        if next_status == WorkOrderStatus.COMPLETED:
            if not has_work_order_document:
                raise DomainError("OPERACIÓN DENEGADA: No se puede completar la Work Order sin el documento 'Work Order' asociado.")
            if not has_maintenance_action_form:
                raise DomainError("OPERACIÓN DENEGADA: No se puede completar la Work Order sin el documento 'Maintenance Action Form' (MAF) asociado.")
                
        work_order.status = next_status
        return work_order


class MaintenanceExecutionService:
    def validate_and_signoff(
        self,
        execution, # MaintenanceTaskExecution
        technician_profile, # TechnicianProfile from personnel_certification
        signature_certificate, # DigitalSignatureCertificate from authorization
        tool_usages: list, # list[ToolUsageRecord]
        human_factors_incidents: list, # list[HumanFactorIncident]
        dual_inspection=None, # MaintenanceDualInspection | None
        inspectors_profiles: list = None, # list[TechnicianProfile]
        is_critical: bool = False
    ) -> None:
        
        # 1. Check if technician profile is active
        if not technician_profile.active:
            raise DomainError("Technician profile is inactive.")
            
        # 2. Check human factors incidents
        critical_count = sum(1 for inc in human_factors_incidents if inc.technician_id == execution.technician_id and inc.severity_level == "CRITICAL")
        high_count = sum(1 for inc in human_factors_incidents if inc.technician_id == execution.technician_id and inc.severity_level == "HIGH")
        
        if critical_count >= 1 or high_count > 2:
            raise DomainError("Technician is suspended due to critical/high human factor incidents.")

        # 3. Check digital signature certificate
        if not signature_certificate or not signature_certificate.active:
            raise DomainError("Digital signature certificate is inactive or missing.")
        if signature_certificate.expires_at < datetime.utcnow():
            raise DomainError("Digital signature certificate has expired.")

        # 4. Check tool usages
        for usage in tool_usages:
            if usage.technician_id == execution.technician_id and usage.task_id == execution.task_id:
                if not usage.calibration_valid_at_usage:
                    raise DomainError("Tool calibration was invalid at time of usage.")
                if usage.damage_detected:
                    raise DomainError("Tool was returned damaged. Execution cannot be signed off.")

        # 5. Dual inspection checks if task is critical
        if is_critical:
            if not dual_inspection:
                raise DomainError("Critical task requires a dual inspection.")
            if dual_inspection.approval_status != "APPROVED":
                raise DomainError("Dual inspection has not been approved.")
            
            # Check inspectors profiles
            if not inspectors_profiles or len(inspectors_profiles) < 2:
                raise DomainError("Critical task requires two qualified inspectors.")
                
            for inspector in inspectors_profiles:
                if inspector.id in {dual_inspection.inspector_id, dual_inspection.second_inspector_id}:
                    if inspector.id == execution.technician_id:
                        raise DomainError("Performing technician cannot act as inspector for dual inspection.")
                    if inspector.current_level != "INSPECTOR" or not inspector.active:
                        raise DomainError("Inspectors must be active and have INSPECTOR certification level.")

