from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError
from app.shared.events.bus import event_bus

from app.modules.assets.domain.models import Asset, AssetStatus, AssetCondition
from app.modules.engine_management.domain.models import (
    EngineAssembly,
    EngineSubModule,
    EngineCycleCounter,
    EngineTrendMonitoring,
    OilAnalysisRecord,
    EngineInstallationHistory,
)
from app.modules.engine_management.domain.services import EngineTrendService

router = APIRouter()

class EngineAssemblyCreate(BaseModel):
    asset_id: UUID
    engine_model: str
    serial_number: str

class RecordTrendRequest(BaseModel):
    engine_assembly_id: UUID
    turbine_temperature_c: float
    oil_pressure_psi: float
    vibration_level: float
    egt_c: float = 0.0
    torque_percent: float = 0.0
    n1_percent: float = 0.0
    n2_percent: float = 0.0
    fuel_flow_gph: float = 0.0
    oil_temperature_c: float = 0.0

class RecordOilAnalysisRequest(BaseModel):
    engine_assembly_id: UUID
    iron_ppm: float
    copper_ppm: float
    silicon_ppm: float
    aluminum_ppm: float = 0.0
    chrome_ppm: float = 0.0
    nickel_ppm: float = 0.0
    contamination_detected: bool = False

@router.post("/engine/assemblies", tags=["engine-management"])
def create_engine_assembly(request: EngineAssemblyCreate, db: Session = Depends(get_db)):
    asset = db.get(Asset, request.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    assembly = EngineAssembly(
        id=uuid4(),
        asset_id=request.asset_id,
        engine_model=request.engine_model,
        serial_number=request.serial_number
    )
    db.add(assembly)
    
    counter = EngineCycleCounter(
        id=uuid4(),
        engine_assembly_id=assembly.id,
        total_operating_hours=0,
        total_start_cycles=0,
        total_ng_cycles=0,
        total_np_cycles=0
    )
    db.add(counter)
    db.commit()
    
    return {
        "engine_assembly_id": str(assembly.id),
        "engine_model": assembly.engine_model,
        "serial_number": assembly.serial_number
    }

@router.get("/engine/assemblies", tags=["engine-management"])
def list_engine_assemblies(db: Session = Depends(get_db)):
    assemblies = db.query(EngineAssembly).all()
    results = []
    for ass in assemblies:
        counter = db.query(EngineCycleCounter).filter_by(engine_assembly_id=ass.id).first()
        results.append({
            "id": str(ass.id),
            "asset_id": str(ass.asset_id),
            "engine_model": ass.engine_model,
            "serial_number": ass.serial_number,
            "hours": float(counter.total_operating_hours) if counter else 0.0,
            "cycles": counter.total_start_cycles if counter else 0
        })
    return results

@router.post("/engine/trend", tags=["engine-management"])
def record_engine_trend(request: RecordTrendRequest, db: Session = Depends(get_db)):
    assembly = db.get(EngineAssembly, request.engine_assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Engine assembly not found")
        
    asset = db.get(Asset, assembly.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Engine asset not found")
        
    try:
        service = EngineTrendService()
        trend, event = service.record_trend(
            engine_assembly=assembly,
            engine_asset=asset,
            turbine_temperature_c=request.turbine_temperature_c,
            oil_pressure_psi=request.oil_pressure_psi,
            vibration_level=request.vibration_level,
            egt_c=request.egt_c,
            torque_percent=request.torque_percent,
            n1_percent=request.n1_percent,
            n2_percent=request.n2_percent,
            fuel_flow_gph=request.fuel_flow_gph,
            oil_temperature_c=request.oil_temperature_c
        )
        db.add(trend)
        if event:
            event_bus.publish(event, db)
            
        db.commit()
        return {
            "trend_id": str(trend.id),
            "recorded_at": str(trend.recorded_at),
            "engine_status": asset.current_status,
            "inspection_required": event is not None
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))

@router.post("/engine/oil-analysis", tags=["engine-management"])
def record_oil_analysis(request: RecordOilAnalysisRequest, db: Session = Depends(get_db)):
    assembly = db.get(EngineAssembly, request.engine_assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Engine assembly not found")
        
    asset = db.get(Asset, assembly.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Engine asset not found")
        
    try:
        service = EngineTrendService()
        record, event = service.record_oil_analysis(
            engine_assembly=assembly,
            engine_asset=asset,
            iron_ppm=request.iron_ppm,
            copper_ppm=request.copper_ppm,
            silicon_ppm=request.silicon_ppm,
            aluminum_ppm=request.aluminum_ppm,
            chrome_ppm=request.chrome_ppm,
            nickel_ppm=request.nickel_ppm,
            contamination_detected=request.contamination_detected
        )
        db.add(record)
        if event:
            event_bus.publish(event, db)
            
        db.commit()
        return {
            "analysis_id": str(record.id),
            "verdict": record.verdict,
            "engine_status": asset.current_status,
            "inspection_required": event is not None
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
