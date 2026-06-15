from uuid import UUID
from sqlalchemy.orm import Session

class ArsenalWorkflowApplicationService:
    def create_maintenance_request(
        self,
        asset_id: UUID,
        priority: str,
        session: Session,
        failure_report_id: UUID | None = None
    ) -> None:
        from app.modules.arsenal_workflow.domain.models import MaintenanceRequest
        from app.modules.organization.domain.models import Department
        from sqlalchemy import select
        from uuid import uuid4
        
        # Buscar departamento de origen por defecto
        dept_stmt = select(Department).limit(1)
        dept = session.scalars(dept_stmt).first()
        dept_id = dept.id if dept else asset_id # Fallback
        
        req = MaintenanceRequest(
            asset_id=asset_id,
            origin_department_id=dept_id,
            failure_report_id=failure_report_id or uuid4(), # Obligatorio por la DB
            requested_by="INTEGRATION_FLOW",
            priority=priority,
            status="CREATED"
        )
        session.add(req)
        session.flush()


    def create_quality_inspection(
        self,
        repair_task_id: UUID,
        session: Session
    ) -> None:
        from app.modules.arsenal_workflow.domain.models import QualityInspection
        from datetime import datetime, timezone
        
        inspection = QualityInspection(
            repair_task_id=repair_task_id,
            inspector_id=repair_task_id, # Fallback
            inspection_date=datetime.now(timezone.utc).date(),
            approved=False,
            inspection_notes="Pending dynamic workflow inspection",
            status="PENDING"
        )
        session.add(inspection)
        session.flush()

    def create_service_release(
        self,
        asset_id: UUID,
        inspection_id: UUID,
        session: Session
    ) -> None:
        from app.modules.arsenal_workflow.domain.models import ServiceRelease
        from datetime import datetime, timezone
        
        release = ServiceRelease(
            asset_id=asset_id,
            quality_inspection_id=inspection_id,
            released_by="CHIEF_INSPECTOR",
            release_date=datetime.now(timezone.utc).date(),
            new_condition="SERVICEABLE",
            status="SERVICEABLE"
        )
        session.add(release)
        session.flush()
