from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.assets.domain.models import Asset, AssetStatus, AssetLifecycleEvent

router = APIRouter()

class TransferComponentRequest(BaseModel):
    component_id: UUID
    destination_department_id: UUID
    performed_by: str
    actor_id: str = "System User"

@router.post("/supply-chain/transfer-to-squadron-storage", tags=["supply-chain"])
def transfer_to_squadron_storage(request: TransferComponentRequest, db: Session = Depends(get_db)):
    component = db.get(Asset, request.component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    before_custodian = component.current_custodian_id
    component.current_custodian_id = request.destination_department_id
    component.current_status = AssetStatus.IN_STOCK
    
    lifecycle_ev = AssetLifecycleEvent(
        id=uuid4(),
        asset_id=component.id,
        event_type="TRANSFERRED",
        recorded_at=date.today(),
        actor=request.performed_by,
        metadata_json={
            "from_custodian_id": str(before_custodian) if before_custodian else None,
            "to_custodian_id": str(request.destination_department_id)
        }
    )
    db.add(lifecycle_ev)
    db.commit()
    return {
        "status": "transferred",
        "component_id": str(component.id),
        "current_custodian_id": str(component.current_custodian_id),
    }
