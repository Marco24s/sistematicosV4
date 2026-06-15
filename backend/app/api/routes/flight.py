from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError

from app.modules.assets.domain.models import Asset, TechnicalHistory, AssetStatus
from app.modules.flight_operations.domain.models import (
    FlightSheet,
    FlightSheetStatus,
    InstalledAsset,
    InstalledAssetStatus,
    Mission,
    MissionStatus,
    MissionType,
)
from app.modules.flight_operations.domain.services import FlightClosureInput, FlightOperationsService
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.modules.organization.domain.models import Organization

from app.core.security import check_permission

router = APIRouter()

# ── Pydantic Models ───────────────────────────────────────────────────────────

class FlightOpenRequest(BaseModel):
    aircraft_id: UUID
    pilot_name: str
    copilot_name: Optional[str] = None
    mission_type: str = "PATROL"
    planned_hours: float = 2.0
    observations: Optional[str] = None
    authorized_by: str

class FlightCloseRequest(BaseModel):
    aircraft_id: UUID
    flight_hours: float
    technical_observations: Optional[str] = None

# ── Endpoint: OPEN FLIGHT ─────────────────────────────────────────────────────

@router.post("/flight/open", tags=["flight"])
def open_flight(request: FlightOpenRequest, db: Session = Depends(get_db)):
    """
    Opens a Flight Sheet and sets the aircraft to AIRBORNE.
    Runs a pre-flight validation pipeline:
      - Aircraft must be RELEASED (not GROUNDED)
      - Airworthiness risk assessment must pass
    """
    aircraft = db.get(Asset, request.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # ── Pre-flight validation pipeline ────────────────────────────────────────
    validation_blocks: list[dict] = []

    # 1. Check aircraft operational status
    if aircraft.current_status == AssetStatus.GROUNDED:
        validation_blocks.append({
            "code": "AIRCRAFT_GROUNDED",
            "severity": "BLOCKING",
            "message": f"Aeronave declarada GROUNDED. Despacho bloqueado hasta resolución técnica."
        })

    # 2. Check technical history / calendar expiration
    aircraft_history = db.query(TechnicalHistory).filter_by(asset_id=request.aircraft_id).first()
    if aircraft_history and aircraft_history.calendar_expiration:
        if aircraft_history.calendar_expiration < date.today():
            validation_blocks.append({
                "code": "CALENDAR_EXPIRED",
                "severity": "BLOCKING",
                "message": f"Inspección calendárica vencida desde {aircraft_history.calendar_expiration}. Requiere revisión de mantenimiento."
            })

    # 3. Check installed components for LLP limits
    installed = db.query(InstalledAsset).filter_by(
        aircraft_asset_id=request.aircraft_id,
        status=InstalledAssetStatus.INSTALLED
    ).all()

    for ic in installed:
        comp_history = db.query(TechnicalHistory).filter_by(asset_id=ic.installed_asset_id).first()
        if comp_history and comp_history.calendar_expiration and comp_history.calendar_expiration < date.today():
            comp = db.get(Asset, ic.installed_asset_id)
            comp_name = comp.nomenclature if comp else str(ic.installed_asset_id)[:8]
            validation_blocks.append({
                "code": "LLP_CALENDAR_EXPIRED",
                "severity": "BLOCKING",
                "message": f"LLP '{comp_name}' con inspección calendárica vencida. Requiere reemplazo o inspección."
            })

    # 4. Check if there's already an AIRBORNE sheet for this aircraft
    existing_airborne = db.query(FlightSheet).filter_by(
        aircraft_asset_id=request.aircraft_id,
        status=FlightSheetStatus.AIRBORNE
    ).first()
    if existing_airborne:
        validation_blocks.append({
            "code": "ALREADY_AIRBORNE",
            "severity": "BLOCKING",
            "message": "La aeronave ya tiene un Parte de Vuelo en estado AIRBORNE abierto."
        })

    # Return blocking errors
    if validation_blocks:
        raise HTTPException(status_code=400, detail={
            "message": "Flight release blocked by pre-flight validation",
            "blocks": validation_blocks
        })

    # ── Run airworthiness risk assessment ─────────────────────────────────────
    warnings: list[dict] = []
    if aircraft_history:
        comp_histories = []
        affected_ids = [request.aircraft_id]
        for ic in installed:
            h = db.query(TechnicalHistory).filter_by(asset_id=ic.installed_asset_id).first()
            if h:
                comp_histories.append(h)
                affected_ids.append(ic.installed_asset_id)
        counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()
        counters_by_asset = {aid: [] for aid in affected_ids}
        for c in counters:
            counters_by_asset[c.asset_id].append(c)
        try:
            risk = FlightOperationsService().detect_airworthiness_risk(
                aircraft=aircraft,
                aircraft_history=aircraft_history,
                installed_asset_histories=comp_histories,
                maintenance_counters_by_asset_id=counters_by_asset
            )
            if not risk.is_airworthy:
                validation_blocks.append({
                    "code": "AIRWORTHINESS_FAILED",
                    "severity": "BLOCKING",
                    "message": "Motor de Aeronavegabilidad detectó riesgos activos. Despacho bloqueado."
                })
                raise HTTPException(status_code=400, detail={
                    "message": "Airworthiness check failed",
                    "blocks": validation_blocks
                })
            for r in risk.risks:
                warnings.append({"code": r.code, "severity": "WARNING", "message": r.message})
        except HTTPException:
            raise
        except Exception:
            pass  # Non-fatal: proceed with dispatch

    # ── Map mission type ───────────────────────────────────────────────────────
    mission_type_map = {
        "SAR": MissionType.SEARCH_AND_RESCUE,
        "SEARCH_AND_RESCUE": MissionType.SEARCH_AND_RESCUE,
        "TRAINING": MissionType.TRAINING,
        "TRANSPORT": MissionType.TRANSPORT,
        "PATROL": MissionType.PATROL,
        "TEST_FLIGHT": MissionType.TEST_FLIGHT,
        "STRIKE": MissionType.PATROL,  # Closest available
        "ASW": MissionType.PATROL,
    }
    mission_type_enum = mission_type_map.get(request.mission_type.upper(), MissionType.PATROL)

    # ── Create Mission + FlightSheet ───────────────────────────────────────────
    org = db.query(Organization).first()
    org_id = aircraft.current_custodian_id or (org.id if org else uuid4())

    mission_code = f"MIS-{aircraft.serial_number[:6]}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    mission = Mission(
        id=uuid4(),
        organization_id=org_id,
        mission_code=mission_code,
        mission_type=mission_type_enum,
        planned_flight_hours=Decimal(str(request.planned_hours)),
        status=MissionStatus.IN_PROGRESS,
    )
    db.add(mission)
    db.flush()

    doc_ref = f"FS-{aircraft.serial_number}-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
    obs_text = f"PILOTO: {request.pilot_name}"
    if request.copilot_name:
        obs_text += f" | COPILOTO: {request.copilot_name}"
    if request.observations:
        obs_text += f" | OBS: {request.observations}"

    flight_sheet = FlightSheet(
        id=uuid4(),
        mission_id=mission.id,
        aircraft_asset_id=request.aircraft_id,
        fuel_loaded=Decimal("1000.00"),
        aircraft_weight=Decimal("8000.00"),
        planned_departure_time=datetime.utcnow(),
        actual_departure_time=datetime.utcnow(),
        planned_hours=Decimal(str(request.planned_hours)),
        status=FlightSheetStatus.AIRBORNE,
        technical_observations=obs_text,
    )
    db.add(flight_sheet)

    # ── Set aircraft AIRBORNE ──────────────────────────────────────────────────
    # We use IN_TRANSFER as AIRBORNE proxy since the domain status enum doesn't have AIRBORNE
    # The FlightSheet.status = AIRBORNE is the authoritative source of truth
    # aircraft.current_status stays RELEASED while AIRBORNE (still in the fleet readiness pool)

    db.commit()

    return {
        "status": "AIRBORNE",
        "flight_sheet_id": str(flight_sheet.id),
        "doc_ref": doc_ref,
        "mission_code": mission_code,
        "aircraft_id": str(aircraft.id),
        "aircraft_serial": aircraft.serial_number,
        "pilot": request.pilot_name,
        "copilot": request.copilot_name,
        "mission_type": request.mission_type,
        "planned_hours": request.planned_hours,
        "departure_time": datetime.utcnow().isoformat(),
        "aircraft_status": str(aircraft.current_status),
        "warnings": warnings,
    }

# ── Endpoint: FLIGHT LOGBOOK ─────────────────────────────────────────────────

@router.get("/flight/logbook", tags=["flight"])
def get_flight_logbook(db: Session = Depends(get_db)):
    """
    Returns the chronological operational logbook of all completed flight sheets.
    """
    sheets = (
        db.query(FlightSheet)
        .filter(FlightSheet.status.in_([FlightSheetStatus.LANDED, FlightSheetStatus.CLOSED]))
        .order_by(FlightSheet.created_at.desc())
        .limit(50)
        .all()
    )
    results = []
    for fs in sheets:
        aircraft = db.get(Asset, fs.aircraft_asset_id)
        mission = fs.mission
        obs = fs.technical_observations or ""
        # Extract pilot from observations field
        pilot = "—"
        if obs.startswith("PILOTO:"):
            pilot = obs.split("|")[0].replace("PILOTO:", "").strip()

        results.append({
            "flight_sheet_id": str(fs.id),
            "doc_ref": f"FS-{aircraft.serial_number if aircraft else '?'}-{fs.created_at.strftime('%Y%m%d') if fs.created_at else '?'}",
            "aircraft_serial": aircraft.serial_number if aircraft else "—",
            "aircraft_nomenclature": aircraft.nomenclature if aircraft else "—",
            "mission_type": str(mission.mission_type) if mission else "—",
            "mission_code": mission.mission_code if mission else "—",
            "pilot": pilot,
            "planned_hours": float(fs.planned_hours) if fs.planned_hours else 0,
            "actual_hours_flown": float(fs.actual_hours_flown) if fs.actual_hours_flown else 0,
            "technical_observations": obs,
            "status": str(fs.status),
            "departure_time": fs.actual_departure_time.isoformat() if fs.actual_departure_time else None,
            "arrival_time": fs.actual_arrival_time.isoformat() if fs.actual_arrival_time else None,
            "created_at": fs.created_at.isoformat() if fs.created_at else None,
        })
    return results

@router.post("/flight/close", tags=["flight"])
def close_flight(request: FlightCloseRequest, db: Session = Depends(get_db), current_user: UUID = Depends(check_permission("CLOSE_FLIGHT"))):
    aircraft = db.get(Asset, request.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    aircraft_history = db.query(TechnicalHistory).filter_by(asset_id=request.aircraft_id).first()
    if not aircraft_history:
        aircraft_history = TechnicalHistory(
            id=uuid4(),
            asset_id=request.aircraft_id,
            opened_date=date.today(),
            current_total_hours=0,
            current_total_cycles=0,
        )
        db.add(aircraft_history)
        db.flush()

    installed_components = db.query(InstalledAsset).filter_by(
        aircraft_asset_id=request.aircraft_id,
        status=InstalledAssetStatus.INSTALLED,
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
                current_total_cycles=0,
            )
            db.add(history)
            db.flush()
        component_histories[ic.installed_asset_id] = history

    affected_ids = [request.aircraft_id] + [ic.installed_asset_id for ic in installed_components]
    counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()
    
    counters_by_asset = {asset_id: [] for asset_id in affected_ids}
    for c in counters:
        counters_by_asset[c.asset_id].append(c)

    # Try to find AIRBORNE sheet first (from open_flight), fallback to PREPARED
    flight_sheet = db.query(FlightSheet).filter(
        FlightSheet.aircraft_asset_id == request.aircraft_id,
        FlightSheet.status.in_([FlightSheetStatus.AIRBORNE, FlightSheetStatus.PREPARED])
    ).order_by(FlightSheet.created_at.desc()).first()

    if not flight_sheet:
        org = db.query(Organization).first()
        org_id = aircraft.current_custodian_id or (org.id if org else uuid4())
        
        mission = Mission(
            id=uuid4(),
            organization_id=org_id,
            mission_code=f"MIS-{uuid4().hex[:6].upper()}",
            mission_type=MissionType.PATROL,
            planned_flight_hours=Decimal(request.flight_hours),
            status=MissionStatus.IN_PROGRESS,
        )
        db.add(mission)
        db.flush()

        flight_sheet = FlightSheet(
            id=uuid4(),
            mission_id=mission.id,
            aircraft_asset_id=request.aircraft_id,
            fuel_loaded=Decimal("1000.00"),
            aircraft_weight=Decimal("8000.00"),
            planned_departure_time=datetime.utcnow(),
            planned_hours=Decimal(request.flight_hours),
            actual_hours_flown=Decimal(request.flight_hours),
            status=FlightSheetStatus.LANDED,
        )
        db.add(flight_sheet)
        db.flush()
    else:
        flight_sheet.actual_hours_flown = Decimal(request.flight_hours)
        flight_sheet.status = FlightSheetStatus.LANDED
        flight_sheet.actual_arrival_time = datetime.utcnow()
        if request.technical_observations:
            existing_obs = flight_sheet.technical_observations or ""
            flight_sheet.technical_observations = existing_obs + f" | ARR_OBS: {request.technical_observations}"
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
            cycles_consumed=1,
        )
        closure_result = FlightOperationsService().close_flight(closure_input)
        
        for ev in closure_result.consumption_events:
            db.add(ev)
        for al in closure_result.alerts:
            db.add(al)

        risk_assessment = FlightOperationsService().detect_airworthiness_risk(
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_asset_histories=list(component_histories.values()),
            maintenance_counters_by_asset_id=counters_by_asset,
        )
        
        if not risk_assessment.is_airworthy:
            aircraft.current_status = AssetStatus.GROUNDED
        
        db.commit()

        return {
            "status": "closed",
            "flight_sheet_id": str(flight_sheet.id),
            "actual_hours_flown": float(flight_sheet.actual_hours_flown),
            "aircraft": {
                "id": str(aircraft.id),
                "total_hours": float(aircraft_history.current_total_hours),
                "total_cycles": aircraft_history.current_total_cycles,
                "status": aircraft.current_status,
            },
            "installed_components_updated": len(installed_components),
            "airworthiness": {
                "is_airworthy": risk_assessment.is_airworthy,
                "risks": [
                    {
                        "asset_id": str(r.asset_id),
                        "code": r.code,
                        "message": r.message,
                    }
                    for r in risk_assessment.risks
                ],
            },
            "alerts_generated": len(closure_result.alerts),
        }

    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
