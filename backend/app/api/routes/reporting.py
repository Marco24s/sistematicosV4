from uuid import UUID, uuid4
from datetime import datetime, date, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db

from app.modules.assets.domain.models import Asset, AssetType, AssetStatus, TechnicalHistory
from app.modules.maintenance.domain.models import FailureReport, WorkOrder, WorkOrderStatus, MaintenanceCounter
from app.modules.reporting_analytics.domain.models import FleetAvailabilityReport, MTBFReport, MTTRReport
from app.modules.maintenance.domain.models import MaintenanceTaskExecution
from app.modules.squadron_operations.domain.models import AircraftConfiguration, MountedComponent, MountedComponentStatus
from app.shared.infrastructure.event_store import StoredDomainEvent

router = APIRouter()

@router.get("/reporting/fleet-availability", tags=["reporting"])
def get_fleet_availability(db: Session = Depends(get_db)):
    aircraft_type_ids = db.query(AssetType.id).filter(AssetType.category == "AIRCRAFT").all()
    aircraft_type_ids = [r[0] for r in aircraft_type_ids]
    
    if not aircraft_type_ids:
        return {"total_aircraft": 0, "available_aircraft": 0, "non_operational_aircraft": 0, "availability_rate": 0.0}
        
    total = db.query(Asset).filter(Asset.asset_type_id.in_(aircraft_type_ids)).count()
    grounded = db.query(Asset).filter(Asset.asset_type_id.in_(aircraft_type_ids), Asset.current_status == AssetStatus.GROUNDED).count()
    available = total - grounded
    rate = (available / total * 100.0) if total > 0 else 0.0
    
    return {
        "total_aircraft": total,
        "available_aircraft": available,
        "non_operational_aircraft": grounded,
        "availability_rate": round(rate, 2)
    }

@router.get("/reporting/mtbf", tags=["reporting"])
def get_mtbf(db: Session = Depends(get_db)):
    types = db.query(AssetType).all()
    results = []
    for t in types:
        assets = db.query(Asset.id).filter_by(asset_type_id=t.id).all()
        asset_ids = [a[0] for a in assets]
        failures = db.query(FailureReport).filter(FailureReport.asset_id.in_(asset_ids)).count()
        mtbf = 1500.0 / failures if failures > 0 else 1500.0
        results.append({
            "asset_type_id": str(t.id),
            "asset_type_name": t.name,
            "failures_count": failures,
            "mtbf_hours": round(mtbf, 1)
        })
    return results

@router.get("/reporting/mttr", tags=["reporting"])
def get_mttr(db: Session = Depends(get_db)):
    completed_orders = db.query(WorkOrder).filter_by(status=WorkOrderStatus.COMPLETED).all()
    total_days = 0.0
    count = len(completed_orders)
    for wo in completed_orders:
        creation = wo.created_at or datetime.now(timezone.utc)
        completion = wo.updated_at or datetime.now(timezone.utc)
        diff = (completion - creation).days + (completion - creation).seconds / 86400.0
        total_days += max(diff, 0.1)
    mttr = (total_days / count) if count > 0 else 2.5
    return {"completed_work_orders_count": count, "mttr_days": round(mttr, 2)}

@router.get("/reporting/timeline", tags=["reporting"])
def get_operational_timeline(db: Session = Depends(get_db)):
    events = db.query(StoredDomainEvent).order_by(StoredDomainEvent.occurred_at.desc()).limit(20).all()
    results = []
    for e in events:
        payload = e.payload or {}
        time_str = e.occurred_at.strftime("%H:%M")
        desc = f"{e.event_type}: {payload}"
        results.append({
            "id": str(e.id),
            "event_type": e.event_type,
            "description": desc,
            "timestamp": time_str,
            "occurred_at": str(e.occurred_at)
        })
    return results

# ─── NUEVOS ENDPOINTS SOLICITADOS ──────────────────────────────────────────

@router.get("/reporting/mtbf/{aircraft_id}", tags=["reporting"])
def get_mtbf_for_aircraft(aircraft_id: UUID, db: Session = Depends(get_db)):
    # Nivel A: MTBF General de Aeronave
    aircraft = db.query(Asset).filter(Asset.id == aircraft_id).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
        
    tech_hist = db.query(TechnicalHistory).filter(TechnicalHistory.asset_id == aircraft_id).first()
    ac_total_hours = tech_hist.current_total_hours if tech_hist else 0
    
    # Contar fallas de la aeronave
    ac_failures = db.query(FailureReport).filter(FailureReport.aircraft_id == aircraft_id).count()
    
    aircraft_mtbf = None
    if ac_failures > 0:
        aircraft_mtbf = ac_total_hours / ac_failures

    # Nivel B: MTBF individual por componente serializado
    active_configuration = db.query(AircraftConfiguration).filter_by(
        aircraft_asset_id=aircraft_id,
        active=True,
    ).first()
    installed_components = []
    if active_configuration:
        installed_components = db.query(MountedComponent).filter_by(
            aircraft_configuration_id=active_configuration.id,
            status=MountedComponentStatus.ACTIVE,
        ).all()
    
    components_mtbf = []
    for ic in installed_components:
        comp_asset = db.query(Asset).filter(Asset.id == ic.asset_id).first()
        comp_tech_hist = db.query(TechnicalHistory).filter(TechnicalHistory.asset_id == ic.asset_id).first()
        comp_hours = comp_tech_hist.current_total_hours if comp_tech_hist else 0
        comp_failures = db.query(FailureReport).filter(FailureReport.asset_id == ic.asset_id).count()
        
        c_mtbf = None
        if comp_failures > 0:
            c_mtbf = comp_hours / comp_failures
            
        components_mtbf.append({
            "component_id": str(ic.asset_id),
            "nomenclature": comp_asset.nomenclature if comp_asset else "Desconocido",
            "serial_number": comp_asset.serial_number if comp_asset else "N/A",
            "position": ic.position_code,
            "total_hours": comp_hours,
            "failures_count": comp_failures,
            "mtbf": round(c_mtbf, 1) if c_mtbf is not None else None,
            "status": "Historial insuficiente para cálculo estadístico" if c_mtbf is None else "Calculado"
        })

    return {
        "aircraft_id": str(aircraft_id),
        "nomenclature": aircraft.nomenclature,
        "serial_number": aircraft.serial_number,
        "total_hours": ac_total_hours,
        "failures_count": ac_failures,
        "aircraft_mtbf": round(aircraft_mtbf, 1) if aircraft_mtbf is not None else None,
        "aircraft_status": "Se requieren más eventos operacionales" if aircraft_mtbf is None else "Calculado",
        "components": components_mtbf
    }

@router.get("/reporting/mttr/{aircraft_id}", tags=["reporting"])
def get_mttr_for_aircraft(aircraft_id: UUID, db: Session = Depends(get_db)):
    aircraft = db.query(Asset).filter(Asset.id == aircraft_id).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
        
    tasks = db.query(MaintenanceTaskExecution).filter(MaintenanceTaskExecution.asset_id == aircraft_id).all()
    
    total_hours = 0.0
    count = len(tasks)
    
    for task in tasks:
        if not task.started_at or not task.completed_at:
            continue
        diff = (task.completed_at - task.started_at).total_seconds() / 3600.0
        total_hours += max(diff, 0.1)
        
    mttr = None
    if count > 0:
        mttr = total_hours / count
        
    return {
        "aircraft_id": str(aircraft_id),
        "nomenclature": aircraft.nomenclature,
        "serial_number": aircraft.serial_number,
        "completed_tasks_count": count,
        "mttr_hours": round(mttr, 2) if mttr is not None else None,
        "status": "Sin datos históricos suficientes" if mttr is None else "Calculado"
    }

@router.get("/reporting/maintenance-forecast/{aircraft_id}", tags=["reporting"])
def get_maintenance_forecast(aircraft_id: UUID, db: Session = Depends(get_db)):
    aircraft = db.query(Asset).filter(Asset.id == aircraft_id).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
        
    # Obtener counters de la aeronave
    ac_counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id == aircraft_id).all()
    
    # Obtener counters de componentes instalados
    active_configuration = db.query(AircraftConfiguration).filter_by(
        aircraft_asset_id=aircraft_id,
        active=True,
    ).first()
    installed_ids = []
    if active_configuration:
        installed = db.query(MountedComponent).filter_by(
            aircraft_configuration_id=active_configuration.id,
            status=MountedComponentStatus.ACTIVE,
        ).all()
        installed_ids = [ic.asset_id for ic in installed]
    comp_counters = []
    if installed_ids:
        comp_counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(installed_ids)).all()
    
    all_counters = ac_counters + comp_counters
    
    forecast = []
    for c in all_counters:
        program = c.maintenance_program
        remaining = c.remaining_usage
        is_aircraft = c.asset_id == aircraft_id
        
        comp_name = aircraft.nomenclature if is_aircraft else "Componente"
        if not is_aircraft:
            comp_asset = db.query(Asset).filter(Asset.id == c.asset_id).first()
            if comp_asset:
                comp_name = f"{comp_asset.nomenclature} ({comp_asset.serial_number})"
                
        forecast.append({
            "id": str(c.id),
            "asset_id": str(c.asset_id),
            "asset_name": comp_name,
            "type": program.interval_type if program else "UNKNOWN",
            "name": program.name if program else "Maintenance Counter",
            "current_value": c.current_usage,
            "expiration_value": program.interval_value if program else None,
            "remaining": remaining
        })
        
    # Ordenar por remanente (los más críticos primero)
    # Filtramos los que no tienen expiration_value para el sort
    forecast.sort(key=lambda x: x["remaining"] if x["remaining"] is not None else 999999)
    
    return {
        "aircraft_id": str(aircraft_id),
        "nomenclature": aircraft.nomenclature,
        "serial_number": aircraft.serial_number,
        "forecast": forecast
    }

@router.get("/reporting/technical-history/{aircraft_id}", tags=["reporting"])
def get_technical_history(aircraft_id: UUID, db: Session = Depends(get_db)):
    # Convertir a string para buscar en payload
    events = db.query(StoredDomainEvent).order_by(StoredDomainEvent.occurred_at.desc()).limit(50).all()
    
    results = []
    for e in events:
        payload = e.payload or {}
        # Filtrar solo eventos de esta aeronave
        if str(payload.get("aircraft_id", "")) == str(aircraft_id) or str(payload.get("asset_id", "")) == str(aircraft_id):
            time_str = e.occurred_at.strftime("%H:%M")
            results.append({
                "id": str(e.id),
                "event_type": e.event_type,
                "payload": payload,
                "timestamp": time_str,
                "occurred_at": str(e.occurred_at)
            })
            
    return {
        "aircraft_id": str(aircraft_id),
        "history": results
    }
