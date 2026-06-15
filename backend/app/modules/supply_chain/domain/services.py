from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.modules.arsenal_workflow.domain.models import AuditEvent
from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, AssetType, TechnicalHistory
from app.modules.document_management.domain.models import AssetDocument, AssetDocumentStatus, DocumentType
from app.modules.supply_chain.domain.models import (
    GoodsReception,
    GoodsReceptionStatus,
    InventoryLocation,
    ProcurementQualityCheck,
    ProvisionPriority,
    ProvisionRequest,
    ProvisionRequestStatus,
    PurchaseOrder,
    PurchaseOrderStatus,
    PurchaseRequest,
    PurchaseRequestStatus,
    StockCondition,
    StockItem,
    StockReservation,
    StockReservationStatus,
    Supplier,
    SupplyChainEvent,
    SupplyChainEventType,
)
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class AuditedResult:
    entity: object
    audit_event: AuditEvent
    supply_chain_event: SupplyChainEvent | None = None


@dataclass(frozen=True)
class ProcurementIncorporationResult:
    quality_check: ProcurementQualityCheck
    asset: Asset | None
    technical_history: TechnicalHistory | None
    initial_document: AssetDocument | None
    stock_item: StockItem | None
    supply_chain_event: SupplyChainEvent
    audit_event: AuditEvent


class SupplyChainService:
    def create_provision_request(
        self,
        requesting_department_id: UUID,
        asset_type_requested: str,
        quantity: int,
        priority: ProvisionPriority,
        requested_by: str,
        requested_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        self._assert_positive_quantity(quantity)
        request = ProvisionRequest(
            id=uuid4(),
            requesting_department_id=requesting_department_id,
            asset_type_requested=asset_type_requested,
            quantity=quantity,
            priority=priority,
            requested_by=requested_by,
            requested_at=requested_at,
            status=ProvisionRequestStatus.CREATED,
        )
        return self._result(
            request,
            actor_id,
            "creo pedido de provision",
            None,
            self._provision_request_state(request),
            self._event(None, SupplyChainEventType.PURCHASE_REQUEST_CREATED, requested_by, None, None, "Provision request created."),
        )

    def check_local_stock(self, stock_items: list[StockItem], required_quantity: int) -> StockItem | None:
        self._assert_positive_quantity(required_quantity)
        for item in stock_items:
            if item.condition == StockCondition.SERVICEABLE and item.available_quantity >= required_quantity:
                return item
        return None

    def reserve_stock(
        self,
        stock_item: StockItem,
        provision_request: ProvisionRequest,
        reserved_quantity: int,
        reserved_at: datetime,
        actor_id: str,
    ) -> AuditedResult:
        self._assert_positive_quantity(reserved_quantity)
        if stock_item.available_quantity < reserved_quantity:
            raise DomainError("Cannot reserve stock beyond available quantity.")
        before_state = self._stock_item_state(stock_item)
        stock_item.reserved_quantity += reserved_quantity
        stock_item.available_quantity -= reserved_quantity
        stock_item.last_updated = reserved_at
        provision_request.status = ProvisionRequestStatus.UNDER_REVIEW
        reservation = StockReservation(
            id=uuid4(),
            stock_item_id=stock_item.id,
            provision_request_id=provision_request.id,
            reserved_quantity=reserved_quantity,
            reserved_at=reserved_at,
            status=StockReservationStatus.ACTIVE,
        )
        return self._result(
            reservation,
            actor_id,
            "reservo stock para provision",
            before_state,
            {"reservation": self._reservation_state(reservation), "stock_item": self._stock_item_state(stock_item)},
            self._event(stock_item.asset_id, SupplyChainEventType.STOCK_RESERVED, actor_id, stock_item.location_id, None, "Stock reserved."),
        )

    def transfer_stock_between_locations(
        self,
        stock_item: StockItem,
        destination_location: InventoryLocation,
        quantity: int,
        performed_by: str,
        timestamp: datetime,
        actor_id: str,
    ) -> tuple[StockItem, StockItem, AuditEvent, SupplyChainEvent]:
        self._assert_positive_quantity(quantity)
        if stock_item.available_quantity < quantity:
            raise DomainError("Cannot transfer unavailable or reserved stock.")

        before_state = self._stock_item_state(stock_item)
        stock_item.quantity -= quantity
        stock_item.available_quantity -= quantity
        stock_item.last_updated = timestamp
        destination_stock = StockItem(
            id=uuid4(),
            asset_id=stock_item.asset_id,
            location_id=destination_location.id,
            quantity=quantity,
            reserved_quantity=0,
            available_quantity=quantity,
            condition=stock_item.condition,
            last_updated=timestamp,
        )
        event = self._event(
            stock_item.asset_id,
            SupplyChainEventType.STOCK_TRANSFERRED,
            performed_by,
            stock_item.location_id,
            destination_location.id,
            "Stock transferred between military logistics locations.",
        )
        audit = self._audit_event(destination_stock, actor_id, "transfirio stock entre ubicaciones", before_state, self._stock_item_state(destination_stock))
        return stock_item, destination_stock, audit, event

    def escalate_to_accessories(self, accessories_stock_items: list[StockItem], required_quantity: int) -> StockItem | None:
        return self.check_local_stock(accessories_stock_items, required_quantity)

    def create_purchase_request(
        self,
        requested_by_department: UUID,
        asset_type: str,
        quantity: int,
        justification: str,
        priority: ProvisionPriority,
        actor_id: str,
    ) -> AuditedResult:
        self._assert_positive_quantity(quantity)
        purchase_request = PurchaseRequest(
            id=uuid4(),
            requested_by_department=requested_by_department,
            asset_type=asset_type,
            quantity=quantity,
            justification=justification,
            priority=priority,
            status=PurchaseRequestStatus.CREATED,
        )
        return self._result(
            purchase_request,
            actor_id,
            "genero solicitud formal de compra",
            None,
            self._purchase_request_state(purchase_request),
            self._event(None, SupplyChainEventType.PURCHASE_REQUEST_CREATED, actor_id, None, None, justification),
        )

    def create_purchase_order(
        self,
        purchase_request: PurchaseRequest,
        supplier: Supplier,
        order_number: str,
        ordered_at: datetime,
        expected_delivery: datetime | None,
        actor_id: str,
    ) -> AuditedResult:
        if not supplier.active:
            raise DomainError("Cannot create purchase order for inactive supplier.")
        purchase_request.status = PurchaseRequestStatus.ORDERED
        order = PurchaseOrder(
            id=uuid4(),
            purchase_request_id=purchase_request.id,
            supplier_id=supplier.id,
            order_number=order_number,
            ordered_at=ordered_at,
            expected_delivery=expected_delivery,
            status=PurchaseOrderStatus.CREATED,
        )
        return self._result(
            order,
            actor_id,
            "emitio orden formal de compra",
            self._purchase_request_state(purchase_request),
            self._purchase_order_state(order),
            self._event(None, SupplyChainEventType.PURCHASE_ORDER_CREATED, actor_id, None, None, f"Purchase order {order_number} created."),
        )

    def receive_purchased_goods(
        self,
        purchase_order: PurchaseOrder,
        received_at: datetime,
        received_by: str,
        documentation_complete: bool,
        actor_id: str,
    ) -> AuditedResult:
        status = GoodsReceptionStatus.PENDING_QUALITY if documentation_complete else GoodsReceptionStatus.REJECTED
        reception = GoodsReception(
            id=uuid4(),
            purchase_order_id=purchase_order.id,
            received_at=received_at,
            received_by=received_by,
            documentation_complete=documentation_complete,
            quality_pending=documentation_complete,
            status=status,
        )
        purchase_order.status = PurchaseOrderStatus.PARTIAL_DELIVERY
        return self._result(
            reception,
            actor_id,
            "registro recepcion inicial de material comprado",
            self._purchase_order_state(purchase_order),
            self._goods_reception_state(reception),
            self._event(None, SupplyChainEventType.GOODS_RECEIVED, received_by, None, None, "Purchased goods received."),
        )

    def execute_procurement_quality_check(
        self,
        goods_reception: GoodsReception,
        inspector_id: UUID,
        documentation_valid: bool,
        physical_condition_valid: bool,
        notes: str | None,
        checked_at: datetime,
        asset_type: AssetType,
        part_number: str,
        serial_number: str,
        nomenclature: str,
        stock_location: InventoryLocation,
        initial_document_type: DocumentType,
        actor_id: str,
    ) -> ProcurementIncorporationResult:
        approved = documentation_valid and physical_condition_valid and goods_reception.documentation_complete
        check = ProcurementQualityCheck(
            id=uuid4(),
            goods_reception_id=goods_reception.id,
            inspector_id=inspector_id,
            documentation_valid=documentation_valid,
            physical_condition_valid=physical_condition_valid,
            approved=approved,
            notes=notes,
            checked_at=checked_at,
        )

        if not approved:
            goods_reception.status = GoodsReceptionStatus.REJECTED
            goods_reception.quality_pending = False
            event = self._event(None, SupplyChainEventType.QUALITY_APPROVED, actor_id, None, stock_location.id, "Quality rejected purchased goods.")
            return ProcurementIncorporationResult(check, None, None, None, None, event, self._audit_event(check, actor_id, "rechazo calidad de material comprado", None, self._quality_check_state(check)))

        goods_reception.status = GoodsReceptionStatus.APPROVED
        goods_reception.quality_pending = False
        asset = Asset(
            id=uuid4(),
            asset_type_id=asset_type.id,
            part_number=part_number,
            serial_number=serial_number,
            nomenclature=nomenclature,
            condition=AssetCondition.SERVICEABLE,
            current_status=AssetStatus.IN_STOCK,
        )
        history = TechnicalHistory(
            id=uuid4(),
            asset_id=asset.id,
            opened_date=checked_at.date(),
            current_total_hours=0,
            current_total_cycles=0,
            notes="Initial technical history created after procurement quality approval.",
        )
        document = AssetDocument(
            id=uuid4(),
            asset_id=asset.id,
            document_type_id=initial_document_type.id,
            document_code=f"INIT-{serial_number}",
            version="1",
            issued_date=checked_at.date(),
            expiration_date=None,
            active=True,
            created_by=actor_id,
            status=AssetDocumentStatus.ACTIVE,
        )
        stock_item = StockItem(
            id=uuid4(),
            asset_id=asset.id,
            location_id=stock_location.id,
            quantity=1,
            reserved_quantity=0,
            available_quantity=1,
            condition=StockCondition.SERVICEABLE,
            last_updated=checked_at,
        )
        event = self._event(asset.id, SupplyChainEventType.QUALITY_APPROVED, actor_id, None, stock_location.id, "Quality approved and incorporated purchased material.")
        audit = self._audit_event(check, actor_id, "aprobo calidad e incorporo material a stock", None, {"asset_id": str(asset.id), "stock_item_id": str(stock_item.id)})
        return ProcurementIncorporationResult(check, asset, history, document, stock_item, event, audit)

    def fulfill_provision_request(
        self,
        provision_request: ProvisionRequest,
        reservation: StockReservation,
        stock_item: StockItem,
        delivered_quantity: int,
        performed_by: str,
        actor_id: str,
    ) -> AuditedResult:
        self._assert_positive_quantity(delivered_quantity)
        if reservation.status != StockReservationStatus.ACTIVE:
            raise DomainError("Provision can only be fulfilled from an active reservation.")
        if reservation.stock_item_id != stock_item.id:
            raise DomainError("Reservation does not belong to the provided stock item.")
        if delivered_quantity > reservation.reserved_quantity:
            raise DomainError("Cannot deliver more than reserved quantity.")

        before_state = {"stock_item": self._stock_item_state(stock_item), "request": self._provision_request_state(provision_request)}
        stock_item.quantity -= delivered_quantity
        stock_item.reserved_quantity -= delivered_quantity
        stock_item.last_updated = datetime.now(timezone.utc)
        reservation.status = StockReservationStatus.CONSUMED
        provision_request.status = ProvisionRequestStatus.FULFILLED if delivered_quantity >= provision_request.quantity else ProvisionRequestStatus.PARTIAL
        return self._result(
            provision_request,
            actor_id,
            "entrego provision a escuadrilla",
            before_state,
            {"stock_item": self._stock_item_state(stock_item), "request": self._provision_request_state(provision_request)},
            self._event(stock_item.asset_id, SupplyChainEventType.PROVISION_DELIVERED, performed_by, stock_item.location_id, None, "Provision delivered to squadron."),
        )

    def _assert_positive_quantity(self, quantity: int) -> None:
        if quantity <= 0:
            raise DomainError("Quantity must be greater than zero.")

    def _result(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None, event: SupplyChainEvent | None) -> AuditedResult:
        return AuditedResult(entity=entity, audit_event=self._audit_event(entity, actor_id, action, before_state, after_state), supply_chain_event=event)

    def _audit_event(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditEvent:
        return AuditEvent(id=uuid4(), actor_id=actor_id, action=action, entity_type=type(entity).__name__, entity_id=entity.id, timestamp=datetime.now(timezone.utc), before_state=before_state, after_state=after_state)

    def _event(self, asset_id: UUID | None, event_type: SupplyChainEventType, performed_by: str, origin_location_id: UUID | None, destination_location_id: UUID | None, notes: str | None) -> SupplyChainEvent:
        return SupplyChainEvent(id=uuid4(), asset_id=asset_id, event_type=event_type, performed_by=performed_by, timestamp=datetime.now(timezone.utc), origin_location_id=origin_location_id, destination_location_id=destination_location_id, notes=notes)

    def _stock_item_state(self, item: StockItem) -> dict:
        return {"id": str(item.id), "asset_id": str(item.asset_id), "location_id": str(item.location_id), "quantity": item.quantity, "reserved_quantity": item.reserved_quantity, "available_quantity": item.available_quantity, "condition": item.condition}

    def _provision_request_state(self, request: ProvisionRequest) -> dict:
        return {"id": str(request.id), "asset_type_requested": request.asset_type_requested, "quantity": request.quantity, "priority": request.priority, "status": request.status}

    def _reservation_state(self, reservation: StockReservation) -> dict:
        return {"id": str(reservation.id), "stock_item_id": str(reservation.stock_item_id), "reserved_quantity": reservation.reserved_quantity, "status": reservation.status}

    def _purchase_request_state(self, request: PurchaseRequest) -> dict:
        return {"id": str(request.id), "asset_type": request.asset_type, "quantity": request.quantity, "status": request.status}

    def _purchase_order_state(self, order: PurchaseOrder) -> dict:
        return {"id": str(order.id), "purchase_request_id": str(order.purchase_request_id), "order_number": order.order_number, "status": order.status}

    def _goods_reception_state(self, reception: GoodsReception) -> dict:
        return {"id": str(reception.id), "purchase_order_id": str(reception.purchase_order_id), "documentation_complete": reception.documentation_complete, "status": reception.status}

    def _quality_check_state(self, check: ProcurementQualityCheck) -> dict:
        return {"id": str(check.id), "goods_reception_id": str(check.goods_reception_id), "approved": check.approved}
