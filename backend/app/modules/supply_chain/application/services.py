from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

class SupplyChainApplicationService:
    def create_stock_item_serviceable(
        self,
        asset_id: UUID,
        location_id: UUID,
        session: Session
    ) -> None:
        from app.modules.supply_chain.domain.models import StockItem, InventoryLocation
        from sqlalchemy import select
        
        # Validar ubicación
        loc = session.get(InventoryLocation, location_id)
        if not loc:
            # Crear ubicación por defecto
            loc = InventoryLocation(
                id=location_id,
                name="Main Storehouse",
                organization_id=uuid4() if 'uuid4' in globals() else asset_id, # Fallback
                location_type="SQUADRON_STORAGE",
                active=True
            )
            session.add(loc)
            session.flush()

        stmt = select(StockItem).where(StockItem.asset_id == asset_id)
        item = session.scalars(stmt).first()
        if item:
            item.condition = "SERVICEABLE"
            item.available_quantity = item.quantity
            item.last_updated = datetime.now(timezone.utc)
        else:
            item = StockItem(
                asset_id=asset_id,
                location_id=location_id,
                quantity=1,
                reserved_quantity=0,
                available_quantity=1,
                condition="SERVICEABLE",
                last_updated=datetime.now(timezone.utc)
            )
            session.add(item)
        session.flush()

    def move_component_to_location(
        self,
        asset_id: UUID,
        destination_location_id: UUID,
        session: Session
    ) -> None:
        from app.modules.supply_chain.domain.models import StockItem
        from sqlalchemy import select
        
        stmt = select(StockItem).where(StockItem.asset_id == asset_id)
        item = session.scalars(stmt).first()
        if item:
            item.location_id = destination_location_id
            item.last_updated = datetime.now(timezone.utc)
        session.flush()
