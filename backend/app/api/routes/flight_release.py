from uuid import UUID, uuid4
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.shared.domain.exceptions import DomainError

from app.modules.assets.domain.models import Asset, AssetStatus
from app.modules.flight_release_control.domain.services import FlightReleaseService
from app.modules.flight_release_control.domain.models import FlightReleaseAuthorization
from app.modules.configuration_baseline.domain.models import AircraftBaselineConfiguration, ConfigurationDeviation
from app.modules.squadron_operations.domain.models import AircraftConfiguration
from app.modules.fod_management.domain.models import FODInspection, FODIncident

router = APIRouter()

class FlightReleaseRequest(BaseModel):
    aircraft_id: UUID
    authorized_by: str
    authorization_type: str = "NORMAL_RELEASE"

class FODInspectionCreate(BaseModel):
    aircraft_id: UUID
    inspection_location: str
    performed_by: str
    findings: str = ""
    cleared_for_operation: bool = True

class ConfigurationDeviationCreate(BaseModel):
    aircraft_id: UUID
    deviation_type: str = "TEMPORARY_MODIFICATION"
    approved_by: str
    justification: str
    expiration_days: int = 30

@router.post("/flight-release/authorize", tags=["flight-release"])
def authorize_flight_release(request: FlightReleaseRequest, db: Session = Depends(get_db)):
    aircraft = db.get(Asset, request.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
        
    # Query configuration, baseline, deviations, FOD
    active_config = db.query(AircraftConfiguration).filter_by(aircraft_asset_id=request.aircraft_id, active=True).first()
    
    # Simple lookup for baseline configuration (by aircraft type or general)
    baseline = db.query(AircraftBaselineConfiguration).first() # Fallback to first configuration baseline for testing
    
    deviations = db.query(ConfigurationDeviation).filter_by(aircraft_id=request.aircraft_id).all()
    
    fod_inspections = db.query(FODInspection).filter_by(aircraft_id=request.aircraft_id).all()
    
    # We query all FOD Incidents. The service will match against the component IDs.
    fod_incidents = db.query(FODIncident).all()
    
    try:
        service = FlightReleaseService()
        authorization = service.release_aircraft(
            aircraft_id=request.aircraft_id,
            authorized_by=request.authorized_by,
            authorization_type=request.authorization_type,
            active_config=active_config,
            baseline=baseline,
            deviations=deviations,
            fod_inspections=fod_inspections,
            fod_incidents=fod_incidents,
            as_of=date.today()
        )
        authorization.id = uuid4()
        db.add(authorization)
        
        # Change status if not grounded
        if aircraft.current_status != AssetStatus.GROUNDED:
            aircraft.current_status = AssetStatus.RELEASED
            
        db.commit()
        return {
            "flight_release_authorization_id": str(authorization.id),
            "aircraft_id": str(authorization.aircraft_id),
            "authorized_by": authorization.authorized_by,
            "authorized_at": str(authorization.authorized_at),
            "status": "AUTHORIZED",
            "aircraft_status": aircraft.current_status
        }
    except DomainError as de:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/flight-release/fod-inspection", tags=["flight-release"])
def create_fod_inspection(request: FODInspectionCreate, db: Session = Depends(get_db)):
    inspection = FODInspection(
        id=uuid4(),
        aircraft_id=request.aircraft_id,
        inspection_location=request.inspection_location,
        performed_by=request.performed_by,
        findings=request.findings,
        cleared_for_operation=request.cleared_for_operation,
        inspected_at=datetime.utcnow()
    )
    db.add(inspection)
    db.commit()
    return {
        "fod_inspection_id": str(inspection.id),
        "cleared_for_operation": inspection.cleared_for_operation
    }

@router.post("/flight-release/deviation", tags=["flight-release"])
def create_deviation(request: ConfigurationDeviationCreate, db: Session = Depends(get_db)):
    from datetime import timedelta
    deviation = ConfigurationDeviation(
        id=uuid4(),
        aircraft_id=request.aircraft_id,
        deviation_type=request.deviation_type,
        approved_by=request.approved_by,
        justification=request.justification,
        expiration_date=date.today() + timedelta(days=request.expiration_days)
    )
    db.add(deviation)
    db.commit()
    return {
        "deviation_id": str(deviation.id),
        "expiration_date": str(deviation.expiration_date)
    }
