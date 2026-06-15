from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.assets.application.schemas import (
    AirworthinessAssessmentRead,
    AssetCreate,
    AssetRead,
    AssetTransferCreate,
    AssetTransferRead,
    AssetTypeCreate,
    AssetTypeRead,
    TechnicalHistoryCreate,
    TechnicalHistoryRead,
)
from app.modules.assets.domain.models import Asset, AssetTransfer, AssetType, TechnicalHistory
from app.modules.assets.domain.services import AirworthinessPolicy, AssetTransferService
from app.modules.assets.infrastructure.repositories import (
    AssetRepository,
    AssetTransferRepository,
    AssetTypeRepository,
    TechnicalHistoryRepository,
)
from app.modules.maintenance.infrastructure.repositories import MaintenanceCounterRepository
from app.shared.domain.exceptions import DomainError

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/types", response_model=AssetTypeRead, status_code=status.HTTP_201_CREATED)
def create_asset_type(payload: AssetTypeCreate, db: Session = Depends(get_db)) -> AssetType:
    asset_type = AssetType(**payload.model_dump())
    return AssetTypeRepository(db).add(asset_type, commit=True)


@router.get("/types", response_model=list[AssetTypeRead])
def list_asset_types(db: Session = Depends(get_db)) -> list[AssetType]:
    return AssetTypeRepository(db).list()


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> Asset:
    asset = Asset(**payload.model_dump())
    return AssetRepository(db).add(asset, commit=True)


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db)) -> list[Asset]:
    return AssetRepository(db).list()


@router.post("/technical-histories", response_model=TechnicalHistoryRead, status_code=status.HTTP_201_CREATED)
def create_technical_history(payload: TechnicalHistoryCreate, db: Session = Depends(get_db)) -> TechnicalHistory:
    history = TechnicalHistory(**payload.model_dump())
    return TechnicalHistoryRepository(db).add(history, commit=True)


@router.post("/transfers", response_model=AssetTransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: AssetTransferCreate, db: Session = Depends(get_db)) -> AssetTransfer:
    asset = AssetRepository(db).get(payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    transfer = AssetTransfer(**payload.model_dump())
    try:
        AssetTransferService().create_transfer(asset, transfer)
    except DomainError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    AssetTransferRepository(db).add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("/{asset_id}/airworthiness", response_model=AirworthinessAssessmentRead)
def assess_airworthiness(asset_id: UUID, db: Session = Depends(get_db)) -> AirworthinessAssessmentRead:
    asset = AssetRepository(db).get_with_operational_state(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    counters = MaintenanceCounterRepository(db).list_by_asset_id(asset_id)
    assessment = AirworthinessPolicy().assess(asset, counters)
    return AirworthinessAssessmentRead(
        asset_id=assessment.asset_id,
        is_airworthy=assessment.is_airworthy,
        findings=[finding.__dict__ for finding in assessment.findings],
    )
