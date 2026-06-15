from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.organization.application.schemas import (
    DepartmentCreate,
    DepartmentRead,
    OrganizationCreate,
    OrganizationRead,
)
from app.modules.organization.domain.models import Department, Organization
from app.modules.organization.infrastructure.repositories import DepartmentRepository, OrganizationRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> Organization:
    organization = Organization(**payload.model_dump())
    return OrganizationRepository(db).add(organization, commit=True)


@router.get("", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)) -> list[Organization]:
    return OrganizationRepository(db).list()


@router.post("/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)) -> Department:
    department = Department(**payload.model_dump())
    return DepartmentRepository(db).add(department, commit=True)


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)) -> list[Department]:
    return DepartmentRepository(db).list()
