from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.maintenance.domain.models import (
    FailureReport,
    MaintenanceCounter,
    MaintenanceProgram,
    WorkOrder,
    WorkOrderStatus,
)
from app.shared.infrastructure.repositories import BaseRepository


class MaintenanceProgramRepository(BaseRepository[MaintenanceProgram]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MaintenanceProgram)


class MaintenanceCounterRepository(BaseRepository[MaintenanceCounter]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MaintenanceCounter)

    def list_by_asset_id(self, asset_id: UUID) -> list[MaintenanceCounter]:
        statement = select(MaintenanceCounter).where(
            MaintenanceCounter.asset_id == asset_id,
            MaintenanceCounter.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class FailureReportRepository(BaseRepository[FailureReport]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, FailureReport)


class WorkOrderRepository(BaseRepository[WorkOrder]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, WorkOrder)

    def list_open_by_failure_report_id(self, failure_report_id: UUID) -> list[WorkOrder]:
        statement = select(WorkOrder).where(
            WorkOrder.failure_report_id == failure_report_id,
            WorkOrder.is_deleted.is_(False),
            WorkOrder.status != WorkOrderStatus.COMPLETED,
        )
        return list(self.session.scalars(statement).all())
