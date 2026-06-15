from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.maintenance.application.schemas import (
    FailureReportCreate,
    FailureReportRead,
    MaintenanceCounterCreate,
    MaintenanceCounterRead,
    MaintenanceProgramCreate,
    MaintenanceProgramRead,
    WorkOrderCreate,
    WorkOrderRead,
)
from app.modules.maintenance.domain.models import FailureReport, MaintenanceCounter, MaintenanceProgram, WorkOrder
from app.modules.maintenance.domain.services import WorkOrderService
from app.modules.maintenance.infrastructure.repositories import (
    FailureReportRepository,
    MaintenanceCounterRepository,
    MaintenanceProgramRepository,
    WorkOrderRepository,
)
from app.shared.domain.exceptions import DomainError

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/programs", response_model=MaintenanceProgramRead, status_code=status.HTTP_201_CREATED)
def create_program(payload: MaintenanceProgramCreate, db: Session = Depends(get_db)) -> MaintenanceProgram:
    program = MaintenanceProgram(**payload.model_dump())
    return MaintenanceProgramRepository(db).add(program, commit=True)


@router.get("/programs", response_model=list[MaintenanceProgramRead])
def list_programs(db: Session = Depends(get_db)) -> list[MaintenanceProgram]:
    return MaintenanceProgramRepository(db).list()


@router.post("/counters", response_model=MaintenanceCounterRead, status_code=status.HTTP_201_CREATED)
def create_counter(payload: MaintenanceCounterCreate, db: Session = Depends(get_db)) -> MaintenanceCounter:
    counter = MaintenanceCounter(**payload.model_dump())
    return MaintenanceCounterRepository(db).add(counter, commit=True)


@router.post("/failure-reports", response_model=FailureReportRead, status_code=status.HTTP_201_CREATED)
def create_failure_report(payload: FailureReportCreate, db: Session = Depends(get_db)) -> FailureReport:
    failure_report = FailureReport(**payload.model_dump())
    return FailureReportRepository(db).add(failure_report, commit=True)


@router.post("/work-orders", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)) -> WorkOrder:
    failure_report = FailureReportRepository(db).get(payload.failure_report_id)
    if failure_report is None:
        raise HTTPException(status_code=404, detail="Failure report not found")

    work_order = WorkOrder(**payload.model_dump())
    try:
        WorkOrderService().create_from_failure_report(failure_report, work_order)
    except DomainError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return WorkOrderRepository(db).add(work_order, commit=True)
