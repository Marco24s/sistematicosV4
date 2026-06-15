from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.domain.models import Asset
from app.modules.organization.domain.models import Department, Organization
from app.shared.domain.models import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class InventoryLocationType(StrEnum):
    PURCHASE_WAREHOUSE = "PURCHASE_WAREHOUSE"
    ACCESSORIES_STORAGE = "ACCESSORIES_STORAGE"
    SUPPORT_STORAGE = "SUPPORT_STORAGE"
    SQUADRON_STORAGE = "SQUADRON_STORAGE"
    TECHNICAL_SECTION_STORAGE = "TECHNICAL_SECTION_STORAGE"


class StockCondition(StrEnum):
    SERVICEABLE = "SERVICEABLE"
    UNSERVICEABLE = "UNSERVICEABLE"
    UNDER_REPAIR = "UNDER_REPAIR"
    PRESERVED = "PRESERVED"
    INSPECTION_REQUIRED = "INSPECTION_REQUIRED"


class ProvisionPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class ProvisionRequestStatus(StrEnum):
    CREATED = "CREATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    FULFILLED = "FULFILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    WAITING_PURCHASE = "WAITING_PURCHASE"


class StockReservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"
    CANCELED = "CANCELED"


class PurchaseRequestStatus(StrEnum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    WAITING_DELIVERY = "WAITING_DELIVERY"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"


class PurchaseOrderStatus(StrEnum):
    CREATED = "CREATED"
    SENT = "SENT"
    PARTIAL_DELIVERY = "PARTIAL_DELIVERY"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class GoodsReceptionStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PENDING_QUALITY = "PENDING_QUALITY"
    PENDING_LOGISTICS_INSPECTION = "PENDING_LOGISTICS_INSPECTION"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class SupplyChainEventType(StrEnum):
    PURCHASE_REQUEST_CREATED = "PURCHASE_REQUEST_CREATED"
    STOCK_RESERVED = "STOCK_RESERVED"
    PURCHASE_ORDER_CREATED = "PURCHASE_ORDER_CREATED"
    GOODS_RECEIVED = "GOODS_RECEIVED"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    STOCK_TRANSFERRED = "STOCK_TRANSFERRED"
    PROVISION_DELIVERED = "PROVISION_DELIVERED"


class InventoryLocation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_inventory_locations"

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    location_type: Mapped[InventoryLocationType] = mapped_column(
        Enum(InventoryLocationType, name="supply_chain_inventory_location_type"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship()


class StockItem(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_stock_items"

    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_inventory_locations.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[StockCondition] = mapped_column(Enum(StockCondition, name="supply_chain_stock_condition"), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Nuevos campos de serializado y aislamiento
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lot_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serialized_inventory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    military_unit_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)


    asset: Mapped[Asset] = relationship()
    location: Mapped[InventoryLocation] = relationship()


class ProvisionRequest(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_provision_requests"

    requesting_department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    asset_type_requested: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[ProvisionPriority] = mapped_column(Enum(ProvisionPriority, name="supply_chain_provision_priority"), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(180), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ProvisionRequestStatus] = mapped_column(
        Enum(ProvisionRequestStatus, name="supply_chain_provision_request_status"),
        default=ProvisionRequestStatus.CREATED,
        nullable=False,
    )

    requesting_department: Mapped[Department] = relationship()


class StockReservation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_stock_reservations"

    stock_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_stock_items.id"), nullable=False, index=True)
    provision_request_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_provision_requests.id"), nullable=False, index=True)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[StockReservationStatus] = mapped_column(
        Enum(StockReservationStatus, name="supply_chain_stock_reservation_status"),
        default=StockReservationStatus.ACTIVE,
        nullable=False,
    )

    stock_item: Mapped[StockItem] = relationship()
    provision_request: Mapped[ProvisionRequest] = relationship()


class PurchaseRequest(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_purchase_requests"

    requested_by_department: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[ProvisionPriority] = mapped_column(Enum(ProvisionPriority, name="supply_chain_purchase_priority"), nullable=False)
    status: Mapped[PurchaseRequestStatus] = mapped_column(
        Enum(PurchaseRequestStatus, name="supply_chain_purchase_request_status"),
        default=PurchaseRequestStatus.CREATED,
        nullable=False,
    )

    department: Mapped[Department] = relationship()


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_suppliers"

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    contact_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_purchase_orders"

    purchase_request_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_purchase_requests.id"), nullable=False, index=True)
    supplier_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_suppliers.id"), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="supply_chain_purchase_order_status"),
        default=PurchaseOrderStatus.CREATED,
        nullable=False,
    )

    purchase_request: Mapped[PurchaseRequest] = relationship()
    supplier: Mapped[Supplier] = relationship()


class GoodsReception(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_goods_receptions"

    purchase_order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_purchase_orders.id"), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_by: Mapped[str] = mapped_column(String(180), nullable=False)
    documentation_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_pending: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[GoodsReceptionStatus] = mapped_column(
        Enum(GoodsReceptionStatus, name="supply_chain_goods_reception_status"),
        default=GoodsReceptionStatus.RECEIVED,
        nullable=False,
    )

    purchase_order: Mapped[PurchaseOrder] = relationship()


class ProcurementQualityCheck(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_procurement_quality_checks"

    goods_reception_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_goods_receptions.id"), nullable=False, index=True)
    inspector_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # 10-point checklist
    supplier_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    po_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pn_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sn_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coc_attached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfg_cert_attached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    packaging_inspected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shelf_life_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    batch_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    physical_condition_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    documentation_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    goods_reception: Mapped[GoodsReception] = relationship()


class SupplyChainEvent(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "supply_chain_events"

    asset_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    event_type: Mapped[SupplyChainEventType] = mapped_column(Enum(SupplyChainEventType, name="supply_chain_event_type"), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(180), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    origin_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_inventory_locations.id"), nullable=True, index=True)
    destination_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_inventory_locations.id"), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset | None] = relationship()
    origin_location: Mapped[InventoryLocation | None] = relationship(foreign_keys=[origin_location_id])
    destination_location: Mapped[InventoryLocation | None] = relationship(foreign_keys=[destination_location_id])


class StockMovementHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "supply_chain_stock_movement_history"

    stock_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_stock_items.id"), nullable=False, index=True)
    from_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_inventory_locations.id"), nullable=True)
    to_location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supply_chain_inventory_locations.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    moved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

