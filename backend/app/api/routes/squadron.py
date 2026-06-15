from uuid import UUID, uuid4
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError

from app.modules.assets.domain.models import Asset, TechnicalHistory, AssetStatus, AssetCondition, AssetLifecycleEvent
from app.modules.squadron_operations.domain.services import SquadronOperationsService
from app.modules.squadron_operations.domain.models import MountedComponent, MountedComponentStatus, AircraftConfiguration
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.modules.flight_operations.domain.services import FlightOperationsService

from app.core.security import check_permission

router = APIRouter()

class RemoveComponentRequest(BaseModel):
    aircraft_id: UUID
    component_id: UUID
    removed_by: str
    actor_id: str = "System User"


class InstallComponentRequest(BaseModel):
    aircraft_id: UUID
    component_id: UUID
    position_code: str
    installed_by: str
    actor_id: str = "System User"


@router.post("/squadron/remove-component", tags=["squadron"])
def remove_component(request: RemoveComponentRequest, db: Session = Depends(get_db)):
    config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=request.aircraft_id, active=True).first()
    if not config:
        raise HTTPException(status_code=404, detail="Active aircraft configuration not found")
    mounted = db.query(MountedComponent).filter_by(
        aircraft_configuration_id=config.id,
        asset_id=request.component_id,
        status=MountedComponentStatus.ACTIVE
    ).first()
    if not mounted:
        raise HTTPException(status_code=404, detail="Mounted component not found or already removed")
    
    component = db.get(Asset, request.component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component asset not found")
        
    history = db.query(TechnicalHistory).filter_by(asset_id=request.component_id).first()
    if not history:
        history = TechnicalHistory(
            id=uuid4(),
            asset_id=request.component_id,
            opened_date=date.today(),
            current_total_hours=0,
            current_total_cycles=0,
        )
        db.add(history)
        db.flush()
        
    try:
        service = SquadronOperationsService()
        result = service.remove_component_from_aircraft(
            mounted_component=mounted,
            component_history=history,
            removed_by=request.removed_by,
            removed_at=datetime.utcnow(),
            actor_id=request.actor_id
        )
        db.add(result.audit_event)
        
        component.current_status = AssetStatus.IN_STOCK
        component.condition = AssetCondition.UNSERVICEABLE
        
        lifecycle_ev = AssetLifecycleEvent(
            id=uuid4(),
            asset_id=component.id,
            event_type="REMOVED_FROM_AIRCRAFT",
            recorded_at=date.today(),
            actor=request.removed_by,
            metadata_json={"aircraft_id": str(request.aircraft_id)}
        )
        db.add(lifecycle_ev)
        db.commit()
        return {
            "status": "removed",
            "mounted_component_id": str(mounted.id),
            "component_status": component.current_status,
            "component_condition": component.condition,
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))


@router.post("/squadron/install-component", tags=["squadron"])
def install_component(request: InstallComponentRequest, db: Session = Depends(get_db), current_user: UUID = Depends(check_permission("INSTALL_COMPONENT"))):
    aircraft = db.get(Asset, request.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
        
    component = db.get(Asset, request.component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
        
    config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=request.aircraft_id, active=True).first()
    if not config:
        config = AircraftConfiguration(
            id=uuid4(),
            aircraft_asset_id=request.aircraft_id,
            configuration_name="Active Configuration",
            active=True
        )
        db.add(config)
        db.flush()
        
    history = db.query(TechnicalHistory).filter_by(asset_id=request.component_id).first()
    if not history:
        history = TechnicalHistory(
            id=uuid4(),
            asset_id=request.component_id,
            opened_date=date.today(),
            current_total_hours=0,
            current_total_cycles=0,
        )
        db.add(history)
        db.flush()
        
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
        
    try:
        service = SquadronOperationsService()
        install_result = service.install_component_on_aircraft(
            aircraft_configuration=config,
            component_asset=component,
            component_history=history,
            position_code=request.position_code,
            installation_date=datetime.utcnow(),
            installed_by=request.installed_by,
            actor_id=request.actor_id
        )
        mounted = install_result.entity
        db.add(mounted)
        db.add(install_result.audit_event)
        
        component.current_status = AssetStatus.INSTALLED
        component.condition = AssetCondition.SERVICEABLE
        
        component_histories = {component.id: history}
        affected_ids = [request.aircraft_id, request.component_id]
        counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()
        counters_by_asset = {asset_id: [] for asset_id in affected_ids}
        for c in counters:
            counters_by_asset[c.asset_id].append(c)
            
        risk_assessment = FlightOperationsService().detect_airworthiness_risk(
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_asset_histories=list(component_histories.values()),
            maintenance_counters_by_asset_id=counters_by_asset
        )
        
        if risk_assessment.is_airworthy:
            aircraft.current_status = AssetStatus.RELEASED
        else:
            aircraft.current_status = AssetStatus.GROUNDED
            
        db.commit()
        return {
            "status": "installed",
            "mounted_id": str(mounted.id),
            "aircraft_status": aircraft.current_status,
            "is_airworthy": risk_assessment.is_airworthy,
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
