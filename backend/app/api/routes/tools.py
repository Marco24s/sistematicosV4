from uuid import UUID, uuid4
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.tool_calibration.domain.models import Tool, CalibrationCertificate, ToolUsageRecord

router = APIRouter()

class CreateToolRequest(BaseModel):
    tool_serial: str
    name: str

class CalibrateToolRequest(BaseModel):
    tool_id: UUID
    calibration_date: date
    calibration_due_date: date
    certification_document_code: str

@router.post("/tools", tags=["tools"])
def create_tool(request: CreateToolRequest, db: Session = Depends(get_db)):
    # Check uniqueness
    existing = db.query(Tool).filter_by(tool_serial=request.tool_serial).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tool serial already exists")
        
    tool = Tool(
        id=uuid4(),
        tool_serial=request.tool_serial,
        name=request.name,
        active=True
    )
    db.add(tool)
    db.commit()
    return {
        "tool_id": str(tool.id),
        "tool_serial": tool.tool_serial,
        "name": tool.name
    }

@router.get("/tools", tags=["tools"])
def list_tools(db: Session = Depends(get_db)):
    tools = db.query(Tool).all()
    results = []
    for t in tools:
        latest_cert = db.query(CalibrationCertificate).filter_by(tool_id=t.id).order_by(CalibrationCertificate.calibration_due_date.desc()).first()
        is_calibrated = False
        if latest_cert and latest_cert.calibration_due_date >= date.today():
            is_calibrated = True
            
        results.append({
            "id": str(t.id),
            "tool_serial": t.tool_serial,
            "name": t.name,
            "active": t.active,
            "is_calibrated": is_calibrated,
            "calibration_due_date": str(latest_cert.calibration_due_date) if latest_cert else None
        })
    return results

@router.post("/tools/calibrate", tags=["tools"])
def calibrate_tool(request: CalibrateToolRequest, db: Session = Depends(get_db)):
    tool = db.get(Tool, request.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
        
    cert = CalibrationCertificate(
        id=uuid4(),
        tool_id=request.tool_id,
        calibration_date=request.calibration_date,
        calibration_due_date=request.calibration_due_date,
        certification_document_code=request.certification_document_code
    )
    db.add(cert)
    
    # reactivate tool if inactive
    tool.active = True
    
    db.commit()
    
    return {
        "certificate_id": str(cert.id),
        "tool_id": str(cert.tool_id),
        "calibration_due_date": str(cert.calibration_due_date)
    }

@router.get("/tools/{tool_id}/calibration-history", tags=["tools"])
def get_calibration_history(tool_id: UUID, db: Session = Depends(get_db)):
    certs = db.query(CalibrationCertificate).filter_by(tool_id=tool_id).order_by(CalibrationCertificate.calibration_date.desc()).all()
    return [
        {
            "id": str(c.id),
            "calibration_date": str(c.calibration_date),
            "calibration_due_date": str(c.calibration_due_date),
            "certification_document_code": c.certification_document_code
        } for c in certs
    ]
