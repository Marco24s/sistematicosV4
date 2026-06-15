from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.configuration.application.schemas import (
    AircraftModelCreate,
    AircraftModelRead,
    ComponentTypeCreate,
    ComponentTypeRead,
    EngineModelCreate,
    EngineModelRead,
)
from app.modules.configuration.domain.models import AircraftModel, ComponentType, EngineModel

router = APIRouter(prefix="/configuration", tags=["configuration"])


@router.post("/aircraft-models", response_model=AircraftModelRead, status_code=status.HTTP_201_CREATED)
def create_aircraft_model(payload: AircraftModelCreate, db: Session = Depends(get_db)) -> AircraftModel:
    model = AircraftModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/aircraft-models", response_model=list[AircraftModelRead])
def list_aircraft_models(db: Session = Depends(get_db)) -> list[AircraftModel]:
    return list(db.query(AircraftModel).order_by(AircraftModel.code).all())


@router.post("/engine-models", response_model=EngineModelRead, status_code=status.HTTP_201_CREATED)
def create_engine_model(payload: EngineModelCreate, db: Session = Depends(get_db)) -> EngineModel:
    model = EngineModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/engine-models", response_model=list[EngineModelRead])
def list_engine_models(db: Session = Depends(get_db)) -> list[EngineModel]:
    return list(db.query(EngineModel).order_by(EngineModel.code).all())


@router.post("/component-types", response_model=ComponentTypeRead, status_code=status.HTTP_201_CREATED)
def create_component_type(payload: ComponentTypeCreate, db: Session = Depends(get_db)) -> ComponentType:
    component_type = ComponentType(**payload.model_dump())
    db.add(component_type)
    db.commit()
    db.refresh(component_type)
    return component_type


@router.get("/component-types", response_model=list[ComponentTypeRead])
def list_component_types(db: Session = Depends(get_db)) -> list[ComponentType]:
    return list(db.query(ComponentType).order_by(ComponentType.code).all())
