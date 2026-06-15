from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, date
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.shared.domain.exceptions import DomainError
from app.shared.events.bus import event_bus

# Imports from various modules
from app.modules.assets.domain.models import Asset, AssetType, TechnicalHistory, AssetStatus, AssetLifecycleEvent, AssetCondition
from app.modules.flight_operations.domain.models import (
    FlightSheet,
    FlightSheetStatus,
    InstalledAsset,
    InstalledAssetStatus,
    Mission,
    MissionStatus,
    MissionType,
    OperationalAlert,
)
from app.modules.flight_operations.domain.services import FlightClosureInput, FlightOperationsService
from app.modules.maintenance.domain.models import FailureReport, FailureSeverity, MaintenanceCounter
from app.modules.maintenance.domain.services import FailureReportService
from app.modules.organization.domain.models import Organization, Department
from app.modules.arsenal_workflow.domain.models import MaintenanceRequest, MaintenanceRequestPriority, MaintenanceRequestStatus
from app.modules.arsenal_workflow.domain.services import ArsenalWorkflowService
from app.modules.workflow_orchestration.domain.events import FailureDetectedEvent

# Setup templates
templates = Jinja2Templates(directory="app/templates")

html_router = APIRouter()


# --- 1) Dashboard principal (/) ---

@html_router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Counts
    aircraft_count = db.query(Asset).join(AssetType).filter(AssetType.category == "AIRCRAFT").count()
    components_count = db.query(Asset).join(AssetType).filter(AssetType.category == "ENGINE").count()
    
    operational_count = db.query(Asset).join(AssetType).filter(
        AssetType.category == "AIRCRAFT",
        Asset.current_status == AssetStatus.RELEASED
    ).count()
    
    grounded_count = db.query(Asset).join(AssetType).filter(
        AssetType.category == "AIRCRAFT",
        Asset.current_status == AssetStatus.GROUNDED
    ).count()

    # Arsenal requests status counting
    arsenal_count = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.status != MaintenanceRequestStatus.COMPLETED
    ).count()

    # Active alerts count
    alerts_count = db.query(OperationalAlert).filter(
        OperationalAlert.status == "OPEN"
    ).count()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "aircraft_count": aircraft_count,
            "components_count": components_count,
            "operational_count": operational_count,
            "grounded_count": grounded_count,
            "arsenal_count": arsenal_count,
            "alerts_count": alerts_count,
        }
    )


# --- 2) Pantalla aeronaves (/aircraft) ---

@html_router.get("/aircraft", response_class=HTMLResponse)
def list_aircraft(request: Request, db: Session = Depends(get_db)):
    aircrafts = (
        db.query(Asset)
        .join(AssetType)
        .filter(AssetType.category == "AIRCRAFT")
        .all()
    )
    return templates.TemplateResponse(
        "aircraft_list.html",
        {
            "request": request,
            "aircrafts": aircrafts,
        }
    )


# --- 3) Detalle aeronave (/aircraft/{id}) ---

@html_router.get("/aircraft/{aircraft_id}", response_class=HTMLResponse)
def aircraft_detail(aircraft_id: UUID, request: Request, db: Session = Depends(get_db)):
    aircraft = db.get(Asset, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    history = db.query(TechnicalHistory).filter_by(asset_id=aircraft_id).first()
    
    # Installed components (InstalledAssetStatus.INSTALLED)
    installed_components = db.query(InstalledAsset).filter_by(
        aircraft_asset_id=aircraft_id,
        status=InstalledAssetStatus.INSTALLED
    ).all()

    # Component hours mapping
    component_hours = {}
    for ic in installed_components:
        comp_hist = db.query(TechnicalHistory).filter_by(asset_id=ic.installed_asset_id).first()
        component_hours[ic.installed_asset_id] = comp_hist.current_total_hours if comp_hist else 0.0

    # Maintenance counters
    affected_ids = [aircraft_id] + [ic.installed_asset_id for ic in installed_components]
    counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()

    # Active restrictions/alerts
    alerts = db.query(OperationalAlert).filter_by(asset_id=aircraft_id, status="OPEN").all()

    return templates.TemplateResponse(
        "aircraft_detail.html",
        {
            "request": request,
            "aircraft": aircraft,
            "history": history,
            "installed_components": installed_components,
            "component_hours": component_hours,
            "counters": counters,
            "alerts": alerts,
        }
    )


# --- Form Handler: Close Flight ---

@html_router.post("/aircraft/{aircraft_id}/close-flight")
def close_flight_form(
    aircraft_id: UUID,
    flight_hours: float = Form(...),
    db: Session = Depends(get_db)
):
    aircraft = db.get(Asset, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # Retrieve or create TechnicalHistory
    aircraft_history = db.query(TechnicalHistory).filter_by(asset_id=aircraft_id).first()
    if not aircraft_history:
        aircraft_history = TechnicalHistory(
            id=uuid4(),
            asset_id=aircraft_id,
            opened_date=date.today(),
            current_total_hours=0,
            current_total_cycles=0
        )
        db.add(aircraft_history)
        db.flush()

    # Installed components
    installed_components = db.query(InstalledAsset).filter_by(
        aircraft_asset_id=aircraft_id,
        status=InstalledAssetStatus.INSTALLED
    ).all()

    component_histories = {}
    for ic in installed_components:
        history = db.query(TechnicalHistory).filter_by(asset_id=ic.installed_asset_id).first()
        if not history:
            history = TechnicalHistory(
                id=uuid4(),
                asset_id=ic.installed_asset_id,
                opened_date=date.today(),
                current_total_hours=0,
                current_total_cycles=0
            )
            db.add(history)
            db.flush()
        component_histories[ic.installed_asset_id] = history

    # Maintenance counters
    affected_ids = [aircraft_id] + [ic.installed_asset_id for ic in installed_components]
    counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()
    
    counters_by_asset = {asset_id: [] for asset_id in affected_ids}
    for c in counters:
        counters_by_asset[c.asset_id].append(c)

    # Mission and FlightSheet setup
    flight_sheet = db.query(FlightSheet).filter_by(
        aircraft_asset_id=aircraft_id,
        status=FlightSheetStatus.PREPARED
    ).first()

    if not flight_sheet:
        org = db.query(Organization).first()
        org_id = aircraft.current_custodian_id or (org.id if org else uuid4())
        
        mission = Mission(
            id=uuid4(),
            organization_id=org_id,
            mission_code=f"MIS-{uuid4().hex[:6].upper()}",
            mission_type=MissionType.PATROL,
            planned_flight_hours=Decimal(flight_hours),
            status=MissionStatus.IN_PROGRESS
        )
        db.add(mission)
        db.flush()

        flight_sheet = FlightSheet(
            id=uuid4(),
            mission_id=mission.id,
            aircraft_asset_id=aircraft_id,
            fuel_loaded=Decimal("1000.00"),
            aircraft_weight=Decimal("8000.00"),
            planned_departure_time=datetime.utcnow(),
            planned_hours=Decimal(flight_hours),
            actual_hours_flown=Decimal(flight_hours),
            status=FlightSheetStatus.LANDED
        )
        db.add(flight_sheet)
        db.flush()
    else:
        flight_sheet.actual_hours_flown = Decimal(flight_hours)
        flight_sheet.status = FlightSheetStatus.LANDED
        mission = flight_sheet.mission

    try:
        closure_input = FlightClosureInput(
            mission=mission,
            flight_sheet=flight_sheet,
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_assets=installed_components,
            installed_asset_histories=component_histories,
            maintenance_counters_by_asset_id=counters_by_asset,
            cycles_consumed=1
        )
        closure_result = FlightOperationsService().close_flight(closure_input)
        
        for ev in closure_result.consumption_events:
            db.add(ev)
        for al in closure_result.alerts:
            db.add(al)

        # Recalculate Airworthiness
        risk_assessment = FlightOperationsService().detect_airworthiness_risk(
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_asset_histories=list(component_histories.values()),
            maintenance_counters_by_asset_id=counters_by_asset
        )
        if not risk_assessment.is_airworthy:
            aircraft.current_status = AssetStatus.GROUNDED
            
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Flight Closure Failed: {str(e)}")

    return RedirectResponse(url=f"/aircraft/{aircraft_id}", status_code=303)


# --- 4) Registrar falla (/report-failure) ---

@html_router.get("/report-failure", response_class=HTMLResponse)
def get_report_failure(request: Request, db: Session = Depends(get_db)):
    aircrafts = db.query(Asset).join(AssetType).filter(AssetType.category == "AIRCRAFT").all()
    components = db.query(Asset).join(AssetType).filter(AssetType.category == "ENGINE").all()
    return templates.TemplateResponse(
        "report_failure.html",
        {
            "request": request,
            "aircrafts": aircrafts,
            "components": components,
        }
    )


@html_router.post("/report-failure", response_class=HTMLResponse)
def post_report_failure(
    request: Request,
    aircraft_id: UUID = Form(...),
    component_id: UUID = Form(...),
    severity: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    aircraft = db.get(Asset, aircraft_id)
    component = db.get(Asset, component_id)

    aircrafts = db.query(Asset).join(AssetType).filter(AssetType.category == "AIRCRAFT").all()
    components = db.query(Asset).join(AssetType).filter(AssetType.category == "ENGINE").all()

    if not aircraft or not component:
        return templates.TemplateResponse(
            "report_failure.html",
            {
                "request": request,
                "aircrafts": aircrafts,
                "components": components,
                "error_msg": "Aeronave o componente no encontrado.",
            }
        )

    try:
        severity_enum = FailureSeverity(severity.upper())
        
        report = FailureReport(
            id=uuid4(),
            asset_id=component_id,
            reported_by="Interface de Operador",
            failure_date=date.today(),
            description=description,
            severity=severity_enum,
            aircraft_id=aircraft_id
        )
        db.add(report)

        # Apply grounding
        FailureReportService().register_failure(component, report)
        aircraft.current_status = AssetStatus.GROUNDED

        # Dispatch FailureDetectedEvent
        event = FailureDetectedEvent(
            aggregate_id=aircraft_id,
            payload={
                "aircraft_id": str(aircraft_id),
                "component_id": str(component_id),
                "severity": severity,
                "description": description
            }
        )
        event_bus.publish(event, db)

        db.commit()

        return templates.TemplateResponse(
            "report_failure.html",
            {
                "request": request,
                "aircrafts": aircrafts,
                "components": components,
                "success_msg": f"Falla registrada con éxito. Aeronave {aircraft.serial_number} y componente {component.serial_number} degradados a GROUNDED.",
            }
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "report_failure.html",
            {
                "request": request,
                "aircrafts": aircrafts,
                "components": components,
                "error_msg": f"Error registrando falla: {str(e)}",
            }
        )


# --- 5) Arsenal workflow monitor (/arsenal) ---

@html_router.get("/arsenal", response_class=HTMLResponse)
def arsenal_monitor(request: Request, db: Session = Depends(get_db)):
    components = db.query(Asset).join(AssetType).filter(
        AssetType.category == "ENGINE",
        Asset.current_status == AssetStatus.GROUNDED
    ).all()
    
    # Active failures to associate
    failures = db.query(FailureReport).all()
    departments = db.query(Department).all()
    
    requests = db.query(MaintenanceRequest).all()

    # Counts
    sent = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == MaintenanceRequestStatus.CREATED).count()
    engineering = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == MaintenanceRequestStatus.UNDER_ENGINEERING_REVIEW).count()
    repair = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.status.in_([MaintenanceRequestStatus.WAITING_REPAIR, MaintenanceRequestStatus.UNDER_REPAIR])
    ).count()
    quality = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == MaintenanceRequestStatus.WAITING_QUALITY).count()
    completed = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == MaintenanceRequestStatus.COMPLETED).count()

    return templates.TemplateResponse(
        "arsenal.html",
        {
            "request": request,
            "components": components,
            "failures": failures,
            "departments": departments,
            "requests": requests,
            "status_counts": {
                "sent": sent,
                "engineering": engineering,
                "repair": repair,
                "quality": quality,
                "completed": completed
            }
        }
    )


@html_router.post("/arsenal/send")
def post_send_to_arsenal(
    component_asset_id: UUID = Form(...),
    source_squadron_id: UUID = Form(...),
    failure_report_id: UUID = Form(...),
    db: Session = Depends(get_db)
):
    component = db.get(Asset, component_asset_id)
    failure_report = db.get(FailureReport, failure_report_id)

    if not component or not failure_report:
        raise HTTPException(status_code=404, detail="Component or Failure report not found")

    try:
        service = ArsenalWorkflowService()
        result = service.create_maintenance_request(
            asset=component,
            failure_report=failure_report,
            origin_department_id=source_squadron_id,
            priority=MaintenanceRequestPriority.NORMAL,
            requested_by="Consola Operativa",
            actor_id="Sistema"
        )
        db.add(result.entity)
        db.add(result.audit_event)

        component.current_status = AssetStatus.IN_TRANSFER

        # Trazabilidad
        lifecycle_ev = AssetLifecycleEvent(
            id=uuid4(),
            asset_id=component_asset_id,
            event_type="SENT_TO_ARSENAL",
            recorded_at=date.today(),
            actor="Consola Operativa",
            metadata_json={"maintenance_request_id": str(result.entity.id)}
        )
        db.add(lifecycle_ev)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Arsenal send failed: {str(e)}")

    return RedirectResponse(url="/arsenal", status_code=303)
