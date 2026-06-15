from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.assets.domain.models import Asset
from app.modules.structural_fatigue.domain.models import StructuralFatigueRecord

router = APIRouter()

class UpdateFatigueRequest(BaseModel):
    asset_id: UUID
    accumulated_cycles: int
    g_force_cycles: int
    landing_cycles: int
    corrosion_index: float
    crack_detection_level: float
    inspection_interval_remaining: int

@router.get("/llp/fatigue/{asset_id}", tags=["llp"])
def get_fatigue_record(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    record = db.query(StructuralFatigueRecord).filter_by(asset_id=asset_id).first()
    if not record:
        # Create a default record if it doesn't exist
        record = StructuralFatigueRecord(
            id=uuid4(),
            asset_id=asset_id,
            accumulated_cycles=0,
            g_force_cycles=0,
            landing_cycles=0,
            corrosion_index=0.0,
            crack_detection_level=0.0,
            inspection_interval_remaining=100
        )
        db.add(record)
        db.commit()
        
    return {
        "asset_id": str(record.asset_id),
        "accumulated_cycles": record.accumulated_cycles,
        "g_force_cycles": record.g_force_cycles,
        "landing_cycles": record.landing_cycles,
        "corrosion_index": record.corrosion_index,
        "crack_detection_level": record.crack_detection_level,
        "inspection_interval_remaining": record.inspection_interval_remaining
    }

@router.post("/llp/fatigue/update", tags=["llp"])
def update_fatigue_record(request: UpdateFatigueRequest, db: Session = Depends(get_db)):
    asset = db.get(Asset, request.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    record = db.query(StructuralFatigueRecord).filter_by(asset_id=request.asset_id).first()
    if not record:
        record = StructuralFatigueRecord(id=uuid4(), asset_id=request.asset_id, accumulated_cycles=0, g_force_cycles=0, landing_cycles=0, corrosion_index=0.0, crack_detection_level=0.0, inspection_interval_remaining=100)
        db.add(record)
        
    record.accumulated_cycles = request.accumulated_cycles
    record.g_force_cycles = request.g_force_cycles
    record.landing_cycles = request.landing_cycles
    record.corrosion_index = request.corrosion_index
    record.crack_detection_level = request.crack_detection_level
    record.inspection_interval_remaining = request.inspection_interval_remaining
    
    db.commit()
    
    return {
        "status": "updated",
        "asset_id": str(record.asset_id),
        "accumulated_cycles": record.accumulated_cycles,
        "inspection_interval_remaining": record.inspection_interval_remaining
    }
