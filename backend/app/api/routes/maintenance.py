from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError
from app.shared.events.bus import event_bus

from app.modules.assets.domain.models import Asset, AssetStatus
from app.modules.maintenance.domain.models import FailureReport, FailureSeverity
from app.modules.maintenance.domain.services import FailureReportService
from app.modules.workflow_orchestration.domain.events import FailureDetectedEvent

from app.core.security import check_permission

router = APIRouter()

class ReportFailureRequest(BaseModel):
    aircraft_id: UUID
    component_id: UUID
    failure_code: str
    severity: str
    description: str
    reported_by: str = "Technician"

@router.post("/maintenance/report-failure", tags=["maintenance"])
def report_failure(request: ReportFailureRequest, db: Session = Depends(get_db), current_user: UUID = Depends(check_permission("ISSUE_AIRWORTHINESS_BLOCK"))):
    aircraft = db.get(Asset, request.aircraft_id)
    component = db.get(Asset, request.component_id)

    if not aircraft or not component:
        raise HTTPException(status_code=404, detail="Aircraft or component not found")

    try:
        severity_enum = FailureSeverity(request.severity.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity value: {request.severity}")

    report = FailureReport(
        id=uuid4(),
        asset_id=request.component_id,
        reported_by=request.reported_by,
        failure_date=date.today(),
        description=request.description,
        severity=severity_enum,
        aircraft_id=request.aircraft_id,
    )
    db.add(report)

    try:
        FailureReportService().register_failure(component, report)
        aircraft.current_status = AssetStatus.GROUNDED

        event = FailureDetectedEvent(
            aggregate_id=request.aircraft_id,
            payload={
                "aircraft_id": str(request.aircraft_id),
                "component_id": str(request.component_id),
                "severity": request.severity,
                "description": request.description,
            },
        )
        event_bus.publish(event, db)

        db.commit()

        return {
            "failure_report_id": str(report.id),
            "component_status": component.current_status,
            "aircraft_status": aircraft.current_status,
            "grounding_applied": True,
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/maintenance/pending", tags=["maintenance"])
def get_pending_maintenance(db: Session = Depends(get_db)):
    # Query FailureReport records
    reports = db.query(FailureReport).all()
    results = []
    for r in reports:
        aircraft = db.get(Asset, r.aircraft_id) if r.aircraft_id else None
        component = db.get(Asset, r.asset_id)
        results.append({
            "id": str(r.id),
            "aircraft_id": str(r.aircraft_id) if r.aircraft_id else None,
            "aircraft_nomenclature": aircraft.nomenclature if aircraft else "N/A",
            "component_id": str(r.asset_id),
            "component_nomenclature": component.nomenclature if component else "N/A",
            "failure_code": r.failure_code if hasattr(r, "failure_code") else "GENERIC",
            "severity": r.severity,
            "description": r.description,
            "reported_by": r.reported_by,
            "failure_date": str(r.failure_date),
        })
    return results
