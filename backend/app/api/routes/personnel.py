from uuid import UUID, uuid4
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.personnel_certification.domain.models import (
    TechnicianProfile,
    TechnicalSpecialization,
    TechnicianCertification,
    CertificationLevel,
)

router = APIRouter()

class CreateTechnicianRequest(BaseModel):
    personnel_id: UUID
    technical_code: str
    join_date: date
    current_level: str # LEVEL_A, LEVEL_B, LEVEL_C, INSPECTOR
    years_of_experience: float
    notes: str = ""

class CreateSpecializationRequest(BaseModel):
    name: str
    description: str = ""

class GrantCertificationRequest(BaseModel):
    technician_profile_id: UUID
    specialization_id: UUID
    certification_level: str
    issued_date: date
    expiration_date: date
    issued_by: str

@router.post("/personnel/technicians", tags=["personnel"])
def create_technician(request: CreateTechnicianRequest, db: Session = Depends(get_db)):
    try:
        level = CertificationLevel(request.current_level.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {request.current_level}")
        
    tech = TechnicianProfile(
        id=uuid4(),
        personnel_id=request.personnel_id,
        technical_code=request.technical_code,
        join_date=request.join_date,
        current_level=level,
        years_of_experience=request.years_of_experience,
        notes=request.notes,
        active=True
    )
    db.add(tech)
    db.commit()
    return {
        "technician_id": str(tech.id),
        "technical_code": tech.technical_code,
        "current_level": tech.current_level
    }

@router.get("/personnel/technicians", tags=["personnel"])
def list_technicians(db: Session = Depends(get_db)):
    techs = db.query(TechnicianProfile).filter_by(active=True).all()
    results = []
    for t in techs:
        certs = db.query(TechnicianCertification).filter_by(technician_profile_id=t.id, active=True).all()
        results.append({
            "id": str(t.id),
            "personnel_id": str(t.personnel_id),
            "technical_code": t.technical_code,
            "join_date": str(t.join_date),
            "current_level": t.current_level,
            "years_of_experience": float(t.years_of_experience),
            "certifications": [
                {
                    "specialization_id": str(c.specialization_id),
                    "certification_level": c.certification_level,
                    "expiration_date": str(c.expiration_date)
                } for c in certs
            ]
        })
    return results

@router.post("/personnel/specializations", tags=["personnel"])
def create_specialization(request: CreateSpecializationRequest, db: Session = Depends(get_db)):
    spec = TechnicalSpecialization(
        id=uuid4(),
        name=request.name.upper(),
        description=request.description
    )
    db.add(spec)
    db.commit()
    return {
        "specialization_id": str(spec.id),
        "name": spec.name
    }

@router.post("/personnel/certifications", tags=["personnel"])
def grant_certification(request: GrantCertificationRequest, db: Session = Depends(get_db)):
    tech = db.get(TechnicianProfile, request.technician_profile_id)
    spec = db.get(TechnicalSpecialization, request.specialization_id)
    
    if not tech or not spec:
        raise HTTPException(status_code=404, detail="Technician profile or specialization not found")
        
    try:
        level = CertificationLevel(request.certification_level.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid certification level: {request.certification_level}")
        
    cert = TechnicianCertification(
        id=uuid4(),
        technician_profile_id=request.technician_profile_id,
        specialization_id=request.specialization_id,
        certification_level=level,
        issued_date=request.issued_date,
        expiration_date=request.expiration_date,
        issued_by=request.issued_by,
        active=True
    )
    db.add(cert)
    db.commit()
    
    return {
        "certification_id": str(cert.id),
        "technician_code": tech.technical_code,
        "specialization_name": spec.name,
        "certification_level": cert.certification_level,
        "expiration_date": str(cert.expiration_date)
    }
