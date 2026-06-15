from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.assets.domain.models import Asset, AssetCondition, AssetStatus, AssetType
from app.modules.document_management.domain.models import AssetDocumentStatus, DocumentType
from app.modules.supply_chain.domain.models import (
    GoodsReceptionStatus,
    InventoryLocation,
    InventoryLocationType,
    ProvisionPriority,
    ProvisionRequestStatus,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
    StockCondition,
    StockItem,
    StockReservationStatus,
    Supplier,
    SupplyChainEventType,
)
from app.modules.supply_chain.domain.services import SupplyChainService
from app.shared.domain.exceptions import DomainError


def make_asset() -> Asset:
    return Asset(
        id=uuid4(),
        asset_type_id=uuid4(),
        part_number="PN-001",
        serial_number="SN-001",
        nomenclature="Hydraulic Pump",
        condition=AssetCondition.SERVICEABLE,
        current_status=AssetStatus.IN_STOCK,
    )


def make_location(location_type=InventoryLocationType.SUPPORT_STORAGE) -> InventoryLocation:
    return InventoryLocation(
        id=uuid4(),
        name="Support Storage",
        organization_id=uuid4(),
        location_type=location_type,
        active=True,
    )


def make_stock_item(asset: Asset, location: InventoryLocation, quantity=3) -> StockItem:
    return StockItem(
        id=uuid4(),
        asset_id=asset.id,
        location_id=location.id,
        quantity=quantity,
        reserved_quantity=0,
        available_quantity=quantity,
        condition=StockCondition.SERVICEABLE,
        last_updated=datetime.now(timezone.utc),
    )


def test_create_provision_request_and_reserve_stock() -> None:
    service = SupplyChainService()
    asset = make_asset()
    location = make_location()
    stock = make_stock_item(asset, location, quantity=2)

    request_result = service.create_provision_request(
        requesting_department_id=uuid4(),
        asset_type_requested="HYDRAULIC_PUMP",
        quantity=1,
        priority=ProvisionPriority.HIGH,
        requested_by="Escuadrilla",
        requested_at=datetime.now(timezone.utc),
        actor_id="squadron-store",
    )
    request = request_result.entity
    assert request.status == ProvisionRequestStatus.CREATED
    assert request_result.supply_chain_event.event_type == SupplyChainEventType.PURCHASE_REQUEST_CREATED

    reservation_result = service.reserve_stock(
        stock_item=stock,
        provision_request=request,
        reserved_quantity=1,
        reserved_at=datetime.now(timezone.utc),
        actor_id="support",
    )

    assert stock.available_quantity == 1
    assert stock.reserved_quantity == 1
    assert reservation_result.entity.status == StockReservationStatus.ACTIVE
    assert reservation_result.supply_chain_event.event_type == SupplyChainEventType.STOCK_RESERVED


def test_transfer_stock_blocks_reserved_quantity() -> None:
    service = SupplyChainService()
    asset = make_asset()
    origin = make_location()
    destination = make_location(InventoryLocationType.SQUADRON_STORAGE)
    stock = make_stock_item(asset, origin, quantity=1)
    stock.available_quantity = 0
    stock.reserved_quantity = 1

    with pytest.raises(DomainError):
        service.transfer_stock_between_locations(
            stock_item=stock,
            destination_location=destination,
            quantity=1,
            performed_by="support",
            timestamp=datetime.now(timezone.utc),
            actor_id="support",
        )


def test_purchase_request_order_and_goods_reception() -> None:
    service = SupplyChainService()
    purchase_request_result = service.create_purchase_request(
        requested_by_department=uuid4(),
        asset_type="HYDRAULIC_PUMP",
        quantity=1,
        justification="No local or central stock available.",
        priority=ProvisionPriority.CRITICAL,
        actor_id="support",
    )
    purchase_request = purchase_request_result.entity
    supplier = Supplier(
        id=uuid4(),
        name="Aero Supplier",
        supplier_code="SUP-001",
        active=True,
    )

    order_result = service.create_purchase_order(
        purchase_request=purchase_request,
        supplier=supplier,
        order_number="PO-001",
        ordered_at=datetime.now(timezone.utc),
        expected_delivery=datetime.now(timezone.utc) + timedelta(days=30),
        actor_id="compras",
    )
    order = order_result.entity
    reception_result = service.receive_purchased_goods(
        purchase_order=order,
        received_at=datetime.now(timezone.utc),
        received_by="almacen-compras",
        documentation_complete=True,
        actor_id="almacen-compras",
    )

    assert purchase_request.status == PurchaseRequestStatus.ORDERED
    assert order.status == PurchaseOrderStatus.PARTIAL_DELIVERY
    assert reception_result.entity.status == GoodsReceptionStatus.PENDING_QUALITY
    assert reception_result.supply_chain_event.event_type == SupplyChainEventType.GOODS_RECEIVED


def test_quality_rejection_does_not_create_asset_or_stock() -> None:
    service = SupplyChainService()
    location = make_location(InventoryLocationType.PURCHASE_WAREHOUSE)
    order = service.create_purchase_order(
        purchase_request=service.create_purchase_request(uuid4(), "PUMP", 1, "Need", ProvisionPriority.NORMAL, "support").entity,
        supplier=Supplier(id=uuid4(), name="Supplier", supplier_code="SUP-002", active=True),
        order_number="PO-002",
        ordered_at=datetime.now(timezone.utc),
        expected_delivery=None,
        actor_id="compras",
    ).entity
    reception = service.receive_purchased_goods(order, datetime.now(timezone.utc), "warehouse", True, "warehouse").entity

    result = service.execute_procurement_quality_check(
        goods_reception=reception,
        inspector_id=uuid4(),
        documentation_valid=False,
        physical_condition_valid=True,
        notes="Missing certificate.",
        checked_at=datetime.now(timezone.utc),
        asset_type=AssetType(id=uuid4(), name="PUMP", category="HYDRAULIC_COMPONENT"),
        part_number="PN-001",
        serial_number="SN-NEW",
        nomenclature="Pump",
        stock_location=location,
        initial_document_type=DocumentType(id=uuid4(), name="TECHNICAL_HISTORY", mandatory=True),
        actor_id="quality",
    )

    assert result.quality_check.approved is False
    assert result.asset is None
    assert result.stock_item is None
    assert reception.status == GoodsReceptionStatus.REJECTED


def test_quality_approval_creates_asset_history_document_and_stock() -> None:
    service = SupplyChainService()
    location = make_location(InventoryLocationType.PURCHASE_WAREHOUSE)
    order = service.create_purchase_order(
        purchase_request=service.create_purchase_request(uuid4(), "PUMP", 1, "Need", ProvisionPriority.NORMAL, "support").entity,
        supplier=Supplier(id=uuid4(), name="Supplier", supplier_code="SUP-003", active=True),
        order_number="PO-003",
        ordered_at=datetime.now(timezone.utc),
        expected_delivery=None,
        actor_id="compras",
    ).entity
    reception = service.receive_purchased_goods(order, datetime.now(timezone.utc), "warehouse", True, "warehouse").entity

    result = service.execute_procurement_quality_check(
        goods_reception=reception,
        inspector_id=uuid4(),
        documentation_valid=True,
        physical_condition_valid=True,
        notes="Accepted.",
        checked_at=datetime.now(timezone.utc),
        asset_type=AssetType(id=uuid4(), name="PUMP", category="HYDRAULIC_COMPONENT"),
        part_number="PN-001",
        serial_number="SN-NEW",
        nomenclature="Pump",
        stock_location=location,
        initial_document_type=DocumentType(id=uuid4(), name="TECHNICAL_HISTORY", mandatory=True),
        actor_id="quality",
    )

    assert result.quality_check.approved is True
    assert result.asset is not None
    assert result.technical_history.asset_id == result.asset.id
    assert result.initial_document.status == AssetDocumentStatus.ACTIVE
    assert result.stock_item.available_quantity == 1
    assert reception.status == GoodsReceptionStatus.APPROVED


def test_fulfill_provision_request_consumes_reservation() -> None:
    service = SupplyChainService()
    asset = make_asset()
    location = make_location()
    stock = make_stock_item(asset, location, quantity=2)
    request = service.create_provision_request(uuid4(), "PUMP", 1, ProvisionPriority.NORMAL, "squadron", datetime.now(timezone.utc), "squadron").entity
    reservation = service.reserve_stock(stock, request, 1, datetime.now(timezone.utc), "support").entity

    result = service.fulfill_provision_request(
        provision_request=request,
        reservation=reservation,
        stock_item=stock,
        delivered_quantity=1,
        performed_by="support",
        actor_id="support",
    )

    assert reservation.status == StockReservationStatus.CONSUMED
    assert request.status == ProvisionRequestStatus.FULFILLED
    assert stock.quantity == 1
    assert stock.reserved_quantity == 0
    assert result.supply_chain_event.event_type == SupplyChainEventType.PROVISION_DELIVERED
