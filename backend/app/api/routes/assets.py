from uuid import UUID, uuid4
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError

from app.modules.assets.domain.models import Asset, AssetType, TechnicalHistory, AssetStatus, AssetLifecycleEvent, AssetCondition, AssetClassification
from app.modules.assets.application.services import AssetsApplicationService
from app.modules.squadron_operations.domain.models import AircraftConfiguration, MountedComponent, MountedComponentStatus

router = APIRouter()

from app.api.routes.auth import get_current_user_payload

class AssetRegisterRequest(BaseModel):
    serial_number: str
    asset_type_id: UUID
    organization_id: UUID
    classification: str
    part_number: str = "PN-GENERIC"
    nomenclature: str = "Generic Asset"
    origin_terminal: str = "UNKNOWN"


@router.post("/assets/register", tags=["assets"])
def register_asset(
    request: AssetRegisterRequest, 
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    try:
        user_id = UUID(payload.get("sub"))
        service = AssetsApplicationService()
        asset = service.register_asset(
            session=db,
            user_id=user_id,
            origin_terminal=request.origin_terminal,
            serial_number=request.serial_number,
            asset_type_id=request.asset_type_id,
            organization_id=request.organization_id,
            classification=request.classification,
            part_number=request.part_number,
            nomenclature=request.nomenclature,
        )
        db.commit()
        return {
            "id": str(asset.id),
            "serial_number": asset.serial_number,
            "nomenclature": asset.nomenclature,
            "classification": asset.classification,
            "status": asset.current_status,
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/assets/types", tags=["assets"])
def get_asset_types(db: Session = Depends(get_db)):
    from app.modules.assets.domain.models import AssetType
    types = db.query(AssetType).all()
    return [{"id": str(t.id), "name": t.name, "category": t.category} for t in types]


class AssetTypeCreateRequest(BaseModel):
    name: str
    category: str


@router.post("/assets/types", tags=["assets"])
def create_asset_type(request: AssetTypeCreateRequest, db: Session = Depends(get_db)):
    from app.modules.assets.domain.models import AssetType
    from sqlalchemy.exc import IntegrityError
    
    new_type = AssetType(id=uuid4(), name=request.name, category=request.category)
    db.add(new_type)
    try:
        db.commit()
        db.refresh(new_type)
        return {"id": str(new_type.id), "name": new_type.name, "category": new_type.category}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Este Modelo y Categoría ya existen en la base de datos.")


@router.get("/assets/organizations", tags=["assets"])
def get_organizations(db: Session = Depends(get_db)):
    from app.modules.organization.domain.models import Organization
    orgs = db.query(Organization).all()
    return [{"id": str(o.id), "name": o.name} for o in orgs]


@router.get("/assets/{asset_id}", tags=["assets"])
def get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    history = db.query(TechnicalHistory).filter_by(asset_id=asset_id).first()
    lifecycle_events = db.query(AssetLifecycleEvent).filter_by(asset_id=asset_id).all()

    return {
        "id": str(asset.id),
        "serial_number": asset.serial_number,
        "part_number": asset.part_number,
        "nomenclature": asset.nomenclature,
        "condition": asset.condition,
        "current_status": asset.current_status,
        "classification": asset.classification,
        "current_custodian_id": str(asset.current_custodian_id) if asset.current_custodian_id else None,
        "technical_history": {
            "opened_date": str(history.opened_date) if history else None,
            "current_total_hours": float(history.current_total_hours) if history else 0.0,
            "current_total_cycles": history.current_total_cycles if history else 0,
            "calendar_expiration": str(history.calendar_expiration) if history and history.calendar_expiration else None,
            "preservation_expiration": str(history.preservation_expiration) if history and history.preservation_expiration else None,
        } if history else None,
        "lifecycle_events": [
            {
                "id": str(ev.id),
                "event_type": ev.event_type,
                "recorded_at": str(ev.recorded_at),
                "actor": ev.actor,
                "metadata_json": ev.metadata_json,
            }
            for ev in lifecycle_events
        ],
    }


@router.get("/components/serviceable", tags=["components"])
def get_serviceable_components(db: Session = Depends(get_db)):
    # Query assets that are not aircraft, condition is SERVICEABLE, and status is IN_STOCK
    components = db.query(Asset).join(AssetType).filter(
        AssetType.category != "AIRCRAFT",
        Asset.condition == AssetCondition.SERVICEABLE,
        Asset.current_status == AssetStatus.IN_STOCK
    ).all()
    results = []
    for c in components:
        history = db.query(TechnicalHistory).filter_by(asset_id=c.id).first()
        results.append({
            "id": str(c.id),
            "nomenclature": c.nomenclature,
            "part_number": c.part_number,
            "serial_number": c.serial_number,
            "hours": float(history.current_total_hours) if history else 0.0,
            "cycles": history.current_total_cycles if history else 0,
        })
    return results


@router.get("/components/{id}", tags=["components"])
def get_component(id: UUID, db: Session = Depends(get_db)):
    # Query asset that is not aircraft
    asset = db.get(Asset, id)
    if not asset:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # check if installed on an aircraft
    mounted = db.query(MountedComponent).filter_by(asset_id=id, status=MountedComponentStatus.ACTIVE).first()
    aircraft_info = None
    if mounted:
        config = db.get(AircraftConfiguration, mounted.aircraft_configuration_id)
        if config:
            aircraft = db.get(Asset, config.aircraft_asset_id)
            if aircraft:
                aircraft_info = {
                    "id": str(aircraft.id),
                    "nomenclature": aircraft.nomenclature,
                    "serial_number": aircraft.serial_number,
                }

    history = db.query(TechnicalHistory).filter_by(asset_id=id).first()

    return {
        "id": str(asset.id),
        "serial_number": asset.serial_number,
        "part_number": asset.part_number,
        "nomenclature": asset.nomenclature,
        "condition": asset.condition,
        "current_status": asset.current_status,
        "classification": asset.classification,
        "current_custodian_id": str(asset.current_custodian_id) if asset.current_custodian_id else None,
        "installed_on": aircraft_info,
        "technical_history": {
            "opened_date": str(history.opened_date) if history else None,
            "current_total_hours": float(history.current_total_hours) if history else 0.0,
            "current_total_cycles": history.current_total_cycles if history else 0,
            "notes": history.notes if history else "",
        } if history else None,
    }


@router.get("/components/{id}/history", tags=["components"])
def get_component_history(id: UUID, db: Session = Depends(get_db)):
    history = db.query(TechnicalHistory).filter_by(asset_id=id).first()
    lifecycle_events = db.query(AssetLifecycleEvent).filter_by(asset_id=id).order_by(AssetLifecycleEvent.recorded_at.desc()).all()
    
    return {
        "component_id": str(id),
        "technical_history": {
            "current_total_hours": float(history.current_total_hours) if history else 0.0,
            "current_total_cycles": history.current_total_cycles if history else 0,
            "notes": history.notes if history else "",
        } if history else None,
        "lifecycle_events": [
            {
                "id": str(ev.id),
                "event_type": ev.event_type,
                "recorded_at": str(ev.recorded_at),
                "actor": ev.actor,
                "metadata_json": ev.metadata_json,
            }
            for ev in lifecycle_events
        ],
    }


@router.get("/aircraft", tags=["aircraft"])
def list_aircraft(db: Session = Depends(get_db)):
    # Query assets where their asset_type.category is 'AIRCRAFT'
    aircraft_list = db.query(Asset).join(AssetType).filter(AssetType.category == "AIRCRAFT").all()
    results = []
    for ac in aircraft_list:
        history = db.query(TechnicalHistory).filter_by(asset_id=ac.id).first()
        results.append({
            "id": str(ac.id),
            "nomenclature": ac.nomenclature,
            "part_number": ac.part_number,
            "serial_number": ac.serial_number,
            "condition": ac.condition,
            "current_status": ac.current_status,
            "total_hours": float(history.current_total_hours) if history else 0.0,
            "total_cycles": history.current_total_cycles if history else 0,
        })
    return results


@router.get("/aircraft/{id}", tags=["aircraft"])
def get_aircraft(id: UUID, db: Session = Depends(get_db)):
    ac = db.get(Asset, id)
    if not ac:
        raise HTTPException(status_code=404, detail="Aircraft not found")
        
    history = db.query(TechnicalHistory).filter_by(asset_id=id).first()
    return {
        "id": str(ac.id),
        "nomenclature": ac.nomenclature,
        "part_number": ac.part_number,
        "serial_number": ac.serial_number,
        "condition": ac.condition,
        "current_status": ac.current_status,
        "total_hours": float(history.current_total_hours) if history else 0.0,
        "total_cycles": history.current_total_cycles if history else 0,
    }


@router.get("/aircraft/{id}/components", tags=["aircraft"])
def get_aircraft_components(id: UUID, db: Session = Depends(get_db)):
    config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=id, active=True).first()
    if not config:
        return []
        
    mounted_list = db.query(MountedComponent).filter_by(
        aircraft_configuration_id=config.id,
        status=MountedComponentStatus.ACTIVE
    ).all()
    
    results = []
    for mc in mounted_list:
        comp = db.get(Asset, mc.asset_id)
        if comp:
            history = db.query(TechnicalHistory).filter_by(asset_id=comp.id).first()
            results.append({
                "id": str(comp.id),
                "position_code": mc.position_code,
                "nomenclature": comp.nomenclature,
                "part_number": comp.part_number,
                "serial_number": comp.serial_number,
                "condition": comp.condition,
                "status": comp.current_status,
                "hours": float(history.current_total_hours) if history else 0.0,
                "cycles": history.current_total_cycles if history else 0,
            })
    return results


@router.get("/fleet/status", tags=["fleet"])
def get_fleet_status(db: Session = Depends(get_db)):
    aircraft_list = db.query(Asset).join(AssetType).filter(AssetType.category == "AIRCRAFT").all()
    total = len(aircraft_list)
    serviceable = sum(1 for ac in aircraft_list if ac.current_status == AssetStatus.RELEASED)
    grounded = sum(1 for ac in aircraft_list if ac.current_status == AssetStatus.GROUNDED)
    
    return {
        "total": total,
        "serviceable": serviceable,
        "grounded": grounded,
    }


@router.get("/aircraft/{id}/timeline", tags=["aircraft"])
def get_aircraft_timeline(id: UUID, db: Session = Depends(get_db)):
    # Gather lifecycle events related to this aircraft or components on this aircraft
    events = db.query(AssetLifecycleEvent).filter_by(asset_id=id).all()
    
    # Also find active configuration to get components
    config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=id, active=True).first()
    component_ids = []
    if config:
        mounted_list = db.query(MountedComponent).filter_by(aircraft_configuration_id=config.id).all()
        component_ids = [mc.asset_id for mc in mounted_list]
        
    # Get all component lifecycle events
    if component_ids:
        comp_events = db.query(AssetLifecycleEvent).filter(AssetLifecycleEvent.asset_id.in_(component_ids)).all()
        events.extend(comp_events)
        
    # Also get all events referencing this aircraft_id in metadata_json
    all_events = db.query(AssetLifecycleEvent).all()
    for ev in all_events:
        if ev.metadata_json and isinstance(ev.metadata_json, dict):
            if ev.metadata_json.get("aircraft_id") == str(id) and ev not in events:
                events.append(ev)
                
    # Sort events chronologically (recorded_at desc/asc)
    events.sort(key=lambda x: x.recorded_at if x.recorded_at else date.min)
    
    results = []
    for ev in events:
        asset_name = "Aeronave"
        asset = db.get(Asset, ev.asset_id)
        if asset:
            asset_name = asset.nomenclature
            
        results.append({
            "id": str(ev.id),
            "asset_id": str(ev.asset_id),
            "asset_name": asset_name,
            "event_type": ev.event_type,
            "recorded_at": str(ev.recorded_at),
            "actor": ev.actor,
            "metadata": ev.metadata_json,
        })
    return results

@router.get("/assets/global-engine/all", tags=["assets"])
def get_global_engine_assets(db: Session = Depends(get_db)):
    assets = db.query(Asset).all()
    result = []
    for asset in assets:
        owner = db.get(Organization, asset.organization_owner_id) if asset.organization_owner_id else None
        custodian = db.get(Department, asset.current_custodian_id) if asset.current_custodian_id else None
        
        result.append({
            "id": str(asset.id),
            "nomenclature": asset.nomenclature,
            "serial_number": asset.serial_number,
            "part_number": asset.part_number,
            "type_category": asset.asset_type.category,
            "condition": asset.condition.value if hasattr(asset.condition, 'value') else asset.condition,
            "status": asset.current_status.value if hasattr(asset.current_status, 'value') else asset.current_status,
            "airworthiness_status": asset.airworthiness_status.value if hasattr(asset.airworthiness_status, 'value') else asset.airworthiness_status,
            "location": asset.current_location or "N/A",
            "owner": owner.name if owner else "N/A",
            "custodian": custodian.name if custodian else "N/A"
        })
    return result
