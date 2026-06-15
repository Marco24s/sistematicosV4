from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError

from app.modules.assets.domain.models import Asset, TechnicalHistory, AssetStatus
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.modules.flight_operations.domain.models import InstalledAsset, InstalledAssetStatus
from app.modules.flight_operations.domain.services import FlightOperationsService
from app.modules.airworthiness_engine.domain.models import AirworthinessDecision

router = APIRouter()

class AirworthinessDecisionRequest(BaseModel):
    aircraft_id: UUID
    decision_status: str # AIRWORTHY, GROUNDED, RESTRICTED_AIRWORTHY
    reason: str
    decided_by: str

@router.get("/airworthiness/evaluate/{aircraft_id}", tags=["airworthiness"])
def evaluate_airworthiness(aircraft_id: UUID, db: Session = Depends(get_db)):
    aircraft = db.get(Asset, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
        
    aircraft_history = db.query(TechnicalHistory).filter_by(asset_id=aircraft_id).first()
    if not aircraft_history:
        aircraft_history = TechnicalHistory(
            id=uuid4(),
            asset_id=aircraft_id,
            opened_date=datetime.now(timezone.utc).date(),
            current_total_hours=0,
            current_total_cycles=0,
        )
        db.add(aircraft_history)
        db.flush()
        
    installed_components = db.query(InstalledAsset).filter_by(
        aircraft_asset_id=aircraft_id,
        status=InstalledAssetStatus.INSTALLED,
    ).all()
    
    component_histories = []
    affected_ids = [aircraft_id]
    for ic in installed_components:
        history = db.query(TechnicalHistory).filter_by(asset_id=ic.installed_asset_id).first()
        if not history:
            history = TechnicalHistory(
                id=uuid4(),
                asset_id=ic.installed_asset_id,
                opened_date=datetime.now(timezone.utc).date(),
                current_total_hours=0,
                current_total_cycles=0,
            )
            db.add(history)
            db.flush()
        component_histories.append(history)
        affected_ids.append(ic.installed_asset_id)
        
    counters = db.query(MaintenanceCounter).filter(MaintenanceCounter.asset_id.in_(affected_ids)).all()
    counters_by_asset = {asset_id: [] for asset_id in affected_ids}
    for c in counters:
        counters_by_asset[c.asset_id].append(c)
        
    try:
        service = FlightOperationsService()
        assessment = service.detect_airworthiness_risk(
            aircraft=aircraft,
            aircraft_history=aircraft_history,
            installed_asset_histories=component_histories,
            maintenance_counters_by_asset_id=counters_by_asset
        )
        
        # Sync aircraft status based on evaluation
        if not assessment.is_airworthy and aircraft.current_status != AssetStatus.GROUNDED:
            aircraft.current_status = AssetStatus.GROUNDED
            db.commit()
            
        return {
            "aircraft_id": str(aircraft_id),
            "is_airworthy": assessment.is_airworthy,
            "aircraft_status": aircraft.current_status,
            "risks": [
                {
                    "asset_id": str(r.asset_id),
                    "code": r.code,
                    "message": r.message
                }
                for r in assessment.risks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airworthiness/decision", tags=["airworthiness"])
def create_airworthiness_decision(request: AirworthinessDecisionRequest, db: Session = Depends(get_db)):
    aircraft = db.get(Asset, request.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
        
    try:
        decision = AirworthinessDecision(
            id=uuid4(),
            aircraft_id=request.aircraft_id,
            decision_status=request.decision_status.upper(),
            reason=request.reason,
            decided_by=request.decided_by,
            decided_at=datetime.utcnow()
        )
        db.add(decision)
        
        if decision.decision_status == "GROUNDED":
            aircraft.current_status = AssetStatus.GROUNDED
        elif decision.decision_status == "AIRWORTHY":
            aircraft.current_status = AssetStatus.RELEASED
            
        db.commit()
        return {
            "decision_id": str(decision.id),
            "aircraft_id": str(decision.aircraft_id),
            "decision_status": decision.decision_status,
            "aircraft_status": aircraft.current_status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
