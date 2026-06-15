from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.supply_chain.domain.models import (
    GoodsReception,
    InventoryLocation,
    ProcurementQualityCheck,
    ProvisionRequest,
    PurchaseOrder,
    PurchaseRequest,
    StockCondition,
    StockItem,
    StockReservation,
    StockReservationStatus,
    Supplier,
    SupplyChainEvent,
)
from app.shared.infrastructure.repositories import BaseRepository


class InventoryLocationRepository(BaseRepository[InventoryLocation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, InventoryLocation)


class StockItemRepository(BaseRepository[StockItem]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, StockItem)

    def list_available_by_location(self, location_id: UUID, condition: StockCondition | None = None) -> list[StockItem]:
        statement = select(StockItem).where(
            StockItem.location_id == location_id,
            StockItem.available_quantity > 0,
            StockItem.is_deleted.is_(False),
        )
        if condition is not None:
            statement = statement.where(StockItem.condition == condition)
        return list(self.session.scalars(statement).all())


class ProvisionRequestRepository(BaseRepository[ProvisionRequest]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ProvisionRequest)


class StockReservationRepository(BaseRepository[StockReservation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, StockReservation)

    def list_active_by_stock_item_id(self, stock_item_id: UUID) -> list[StockReservation]:
        statement = select(StockReservation).where(
            StockReservation.stock_item_id == stock_item_id,
            StockReservation.status == StockReservationStatus.ACTIVE,
            StockReservation.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class PurchaseRequestRepository(BaseRepository[PurchaseRequest]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, PurchaseRequest)


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Supplier)


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, PurchaseOrder)


class GoodsReceptionRepository(BaseRepository[GoodsReception]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, GoodsReception)


class ProcurementQualityCheckRepository(BaseRepository[ProcurementQualityCheck]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ProcurementQualityCheck)


class SupplyChainEventRepository(BaseRepository[SupplyChainEvent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, SupplyChainEvent)
