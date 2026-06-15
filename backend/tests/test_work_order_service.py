from uuid import uuid4

import pytest

from app.modules.maintenance.domain.models import WorkOrder, WorkOrderPriority, WorkOrderStatus
from app.modules.maintenance.domain.services import WorkOrderService
from app.shared.domain.exceptions import DomainError


def test_work_order_rejects_invalid_transition() -> None:
    work_order = WorkOrder(
        id=uuid4(),
        failure_report_id=uuid4(),
        origin_department_id=uuid4(),
        assigned_department_id=uuid4(),
        priority=WorkOrderPriority.ROUTINE,
        status=WorkOrderStatus.CREATED,
    )

    with pytest.raises(DomainError):
        WorkOrderService().transition(work_order, WorkOrderStatus.COMPLETED)
