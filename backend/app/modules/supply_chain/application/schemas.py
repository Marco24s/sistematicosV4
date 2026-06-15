from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.supply_chain.domain.models import (
    GoodsReceptionStatus,
    InventoryLocationType,
    ProvisionPriority,
    ProvisionRequestStatus,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
    StockCondition,
    StockReservationStatus,
    SupplyChainEventType,
)


class InventoryLocationRead(BaseModel):
    id: UUID
    name: str
    organization_id: UUID
    location_type: InventoryLocationType
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class StockItemRead(BaseModel):
    id: UUID
    asset_id: UUID
    location_id: UUID
    quantity: int
    reserved_quantity: int
    available_quantity: int
    condition: StockCondition
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ProvisionRequestRead(BaseModel):
    id: UUID
    requesting_department_id: UUID
    asset_type_requested: str
    quantity: int
    priority: ProvisionPriority
    requested_by: str
    requested_at: datetime
    status: ProvisionRequestStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class StockReservationRead(BaseModel):
    id: UUID
    stock_item_id: UUID
    provision_request_id: UUID
    reserved_quantity: int
    reserved_at: datetime
    status: StockReservationStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class PurchaseRequestRead(BaseModel):
    id: UUID
    requested_by_department: UUID
    asset_type: str
    quantity: int
    justification: str
    priority: ProvisionPriority
    status: PurchaseRequestStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SupplierRead(BaseModel):
    id: UUID
    name: str
    supplier_code: str
    contact_name: str | None
    email: str | None
    phone: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    id: UUID
    purchase_request_id: UUID
    supplier_id: UUID
    order_number: str
    ordered_at: datetime
    expected_delivery: datetime | None
    status: PurchaseOrderStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class GoodsReceptionRead(BaseModel):
    id: UUID
    purchase_order_id: UUID
    received_at: datetime
    received_by: str
    documentation_complete: bool
    quality_pending: bool
    status: GoodsReceptionStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SupplyChainEventRead(BaseModel):
    id: UUID
    asset_id: UUID | None
    event_type: SupplyChainEventType
    performed_by: str
    timestamp: datetime
    origin_location_id: UUID | None
    destination_location_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
