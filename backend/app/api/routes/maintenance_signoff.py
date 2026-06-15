from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.maintenance.domain.models import MaintenanceTaskExecution, MaintenanceDualInspection
from app.modules.personnel_certification.domain.models import TechnicianProfile, CertificationLevel
from app.modules.authorization.domain.models import DigitalSignatureCertificate

router = APIRouter()

class TaskExecutionRequest(BaseModel):
    task_id: UUID
    asset_id: UUID
    technician_id: UUID
    digital_signature_hash: str

class DualInspectionRequest(BaseModel):
    execution_id: UUID
    inspector_id: UUID
    second_inspector_id: UUID

@router.post("/maintenance/signoff/execute", tags=["maintenance-signoff"])
def execute_task_signoff(request: TaskExecutionRequest, db: Session = Depends(get_db)):
    tech = db.get(TechnicianProfile, request.technician_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Technician profile not found")
        
    execution = MaintenanceTaskExecution(
        id=uuid4(),
        task_id=request.task_id,
        asset_id=request.asset_id,
        technician_id=request.technician_id,
        certification_level=tech.current_level,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        digital_signature_hash=request.digital_signature_hash
    )
    db.add(execution)
    db.commit()
    
    return {
        "execution_id": str(execution.id),
        "status": "SIGNED_OFF",
        "certification_level": execution.certification_level
    }

@router.post("/maintenance/signoff/dual-inspect", tags=["maintenance-signoff"])
def execute_dual_inspection(request: DualInspectionRequest, db: Session = Depends(get_db)):
    execution = db.get(MaintenanceTaskExecution, request.execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Maintenance task execution not found")
        
    insp1 = db.get(TechnicianProfile, request.inspector_id)
    insp2 = db.get(TechnicianProfile, request.second_inspector_id)
    if not insp1 or not insp2:
        raise HTTPException(status_code=404, detail="One or both inspectors not found")
        
    if insp1.current_level != CertificationLevel.INSPECTOR or insp2.current_level != CertificationLevel.INSPECTOR:
        raise HTTPException(status_code=400, detail="Both signees for critical dual inspections must be certified Inspectors")
        
    # Check digital certificate presence
    cert1 = db.query(DigitalSignatureCertificate).filter_by(user_id=request.inspector_id, active=True).first()
    cert2 = db.query(DigitalSignatureCertificate).filter_by(user_id=request.second_inspector_id, active=True).first()
    
    if not cert1 or not cert2:
        raise HTTPException(status_code=400, detail="Active digital signature certificates required for both inspectors")
        
    dual = MaintenanceDualInspection(
        id=uuid4(),
        execution_id=request.execution_id,
        inspector_id=request.inspector_id,
        second_inspector_id=request.second_inspector_id,
        approval_status="APPROVED"
    )
    db.add(dual)
    db.commit()
    
    return {
        "dual_inspection_id": str(dual.id),
        "execution_id": str(dual.execution_id),
        "approval_status": dual.approval_status
    }
