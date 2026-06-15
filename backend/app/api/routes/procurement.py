from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.supply_chain.domain.models import (
    ProvisionRequest,
    ProvisionPriority,
    ProvisionRequestStatus,
    PurchaseRequest, PurchaseRequestStatus,
    Supplier,
    PurchaseOrder, PurchaseOrderStatus,
    GoodsReception, GoodsReceptionStatus,
    ProcurementQualityCheck,
    StockItem, StockCondition,
    SupplyChainEvent, SupplyChainEventType,
    InventoryLocation, InventoryLocationType
)

router = APIRouter()

class CreateProvisionRequest(BaseModel):
    requesting_department_id: UUID
    asset_type_requested: str
    quantity: int
    priority: str = "NORMAL"
    requested_by: str

class UpdateProvisionStatusRequest(BaseModel):
    request_id: UUID
    status: str

@router.post("/procurement/provision-requests", tags=["procurement"])
def create_provision_request(request: CreateProvisionRequest, db: Session = Depends(get_db)):
    try:
        priority_enum = ProvisionPriority(request.priority.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {request.priority}")
        
    provision = ProvisionRequest(
        id=uuid4(),
        requesting_department_id=request.requesting_department_id,
        asset_type_requested=request.asset_type_requested,
        quantity=request.quantity,
        priority=priority_enum,
        requested_by=request.requested_by,
        requested_at=datetime.utcnow(),
        status=ProvisionRequestStatus.CREATED
    )
    db.add(provision)
    db.commit()
    
    return {
        "provision_request_id": str(provision.id),
        "status": provision.status,
        "asset_type_requested": provision.asset_type_requested
    }

@router.get("/procurement/provision-requests", tags=["procurement"])
def list_provision_requests(db: Session = Depends(get_db)):
    requests = db.query(ProvisionRequest).all()
    return [
        {
            "id": str(r.id),
            "requesting_department_id": str(r.requesting_department_id),
            "asset_type_requested": r.asset_type_requested,
            "quantity": r.quantity,
            "priority": r.priority,
            "requested_by": r.requested_by,
            "requested_at": str(r.requested_at),
            "status": r.status
        } for r in requests
    ]

@router.post("/procurement/provision-requests/status", tags=["procurement"])
def update_provision_status(request: UpdateProvisionStatusRequest, db: Session = Depends(get_db)):
    provision = db.get(ProvisionRequest, request.request_id)
    if not provision:
        raise HTTPException(status_code=404, detail="Provision request not found")
        
    try:
        status_enum = ProvisionRequestStatus(request.status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        
    provision.status = status_enum
    db.commit()
    
    return {
        "provision_request_id": str(provision.id),
        "status": provision.status
    }

class CreatePurchaseRequest(BaseModel):
    requested_by_department: UUID
    asset_type: str
    quantity: int
    justification: str
    priority: str

class CreatePurchaseOrder(BaseModel):
    purchase_request_id: UUID
    supplier_id: UUID
    order_number: str

class CreateGoodsReception(BaseModel):
    purchase_order_id: UUID
    received_by: str

class LogisticsInspectionRequest(BaseModel):
    goods_reception_id: UUID
    inspector_id: UUID
    supplier_verified: bool
    po_validated: bool
    pn_validated: bool
    sn_validated: bool
    coc_attached: bool
    mfg_cert_attached: bool
    packaging_inspected: bool
    shelf_life_verified: bool
    batch_verified: bool
    physical_condition_valid: bool
    notes: str | None = None
    serial_number: str | None = None

@router.get("/procurement/purchase-requests", tags=["procurement"])
def list_purchase_requests(db: Session = Depends(get_db)):
    prs = db.query(PurchaseRequest).all()
    return prs

@router.post("/procurement/purchase-requests", tags=["procurement"])
def create_purchase_request(req: CreatePurchaseRequest, db: Session = Depends(get_db)):
    try:
        priority_enum = ProvisionPriority(req.priority.upper())
    except ValueError:
        priority_enum = ProvisionPriority.NORMAL

    pr = PurchaseRequest(
        id=uuid4(),
        requested_by_department=req.requested_by_department,
        asset_type=req.asset_type,
        quantity=req.quantity,
        justification=req.justification,
        priority=priority_enum,
        status=PurchaseRequestStatus.APPROVED
    )
    db.add(pr)
    db.commit()
    return pr

@router.get("/procurement/suppliers", tags=["procurement"])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.active == True).all()

@router.get("/procurement/purchase-orders", tags=["procurement"])
def list_purchase_orders(db: Session = Depends(get_db)):
    return db.query(PurchaseOrder).all()

@router.post("/procurement/purchase-orders", tags=["procurement"])
def create_purchase_order(req: CreatePurchaseOrder, db: Session = Depends(get_db)):
    po = PurchaseOrder(
        id=uuid4(),
        purchase_request_id=req.purchase_request_id,
        supplier_id=req.supplier_id,
        order_number=req.order_number,
        ordered_at=datetime.utcnow(),
        status=PurchaseOrderStatus.SENT
    )
    pr = db.get(PurchaseRequest, req.purchase_request_id)
    if pr:
        pr.status = PurchaseRequestStatus.ORDERED
    db.add(po)
    db.commit()
    return po

@router.get("/procurement/goods-receptions", tags=["procurement"])
def list_goods_receptions(db: Session = Depends(get_db)):
    return db.query(GoodsReception).all()

@router.post("/procurement/purchase-orders/{id}/receive", tags=["procurement"])
def receive_goods(id: UUID, req: CreateGoodsReception, db: Session = Depends(get_db)):
    reception = GoodsReception(
        id=uuid4(),
        purchase_order_id=id,
        received_at=datetime.utcnow(),
        received_by=req.received_by,
        status=GoodsReceptionStatus.PENDING_LOGISTICS_INSPECTION
    )
    po = db.get(PurchaseOrder, id)
    if po:
        po.status = PurchaseOrderStatus.COMPLETED
        if po.purchase_request:
            po.purchase_request.status = PurchaseRequestStatus.RECEIVED
    db.add(reception)
    db.commit()
    return reception

@router.post("/procurement/receptions/{id}/inspect", tags=["procurement"])
def inspect_reception(id: UUID, req: LogisticsInspectionRequest, db: Session = Depends(get_db)):
    reception = db.get(GoodsReception, id)
    if not reception:
        raise HTTPException(status_code=404, detail="Reception not found")
        
    approved = all([
        req.supplier_verified, req.po_validated, req.pn_validated, req.sn_validated,
        req.coc_attached, req.mfg_cert_attached, req.packaging_inspected,
        req.shelf_life_verified, req.batch_verified, req.physical_condition_valid
    ])
    
    check = ProcurementQualityCheck(
        id=uuid4(),
        goods_reception_id=id,
        inspector_id=req.inspector_id,
        supplier_verified=req.supplier_verified,
        po_validated=req.po_validated,
        pn_validated=req.pn_validated,
        sn_validated=req.sn_validated,
        coc_attached=req.coc_attached,
        mfg_cert_attached=req.mfg_cert_attached,
        packaging_inspected=req.packaging_inspected,
        shelf_life_verified=req.shelf_life_verified,
        batch_verified=req.batch_verified,
        physical_condition_valid=req.physical_condition_valid,
        documentation_valid=True,
        approved=approved,
        notes=req.notes,
        checked_at=datetime.utcnow()
    )
    db.add(check)
    
    if approved:
        reception.status = GoodsReceptionStatus.APPROVED
        
        # Transfer custody automatically to Arsenal Storage
        arsenal_storage = db.query(InventoryLocation).filter(
            InventoryLocation.location_type == InventoryLocationType.TECHNICAL_SECTION_STORAGE
        ).first()
        
        if arsenal_storage:
            from app.modules.assets.domain.models import Asset
            asset = db.query(Asset).filter(Asset.nomenclature.ilike(f"%{reception.purchase_order.purchase_request.asset_type}%")).first()
            if not asset:
                asset = db.query(Asset).first()
            
            stock_item = StockItem(
                id=uuid4(),
                asset_id=asset.id,
                location_id=arsenal_storage.id,
                quantity=reception.purchase_order.purchase_request.quantity,
                available_quantity=reception.purchase_order.purchase_request.quantity,
                condition=StockCondition.SERVICEABLE,
                last_updated=datetime.utcnow(),
                serial_number=req.serial_number,
                serialized_inventory=True
            )
            db.add(stock_item)
            
            event = SupplyChainEvent(
                id=uuid4(),
                asset_id=asset.id,
                event_type=SupplyChainEventType.STOCK_TRANSFERRED,
                performed_by=str(req.inspector_id),
                timestamp=datetime.utcnow(),
                destination_location_id=arsenal_storage.id,
                notes=f"STOCK_TRANSFERRED_TO_ARSENAL: Validated through Logistics Inspection. PO: {reception.purchase_order.order_number}"
            )
            db.add(event)
    else:
        reception.status = GoodsReceptionStatus.REJECTED
        
    db.commit()
    return {"status": reception.status, "approved": approved}
