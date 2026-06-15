from uuid import UUID
from sqlalchemy.orm import Session

class AssetsApplicationService:
    def create_asset_from_purchase(
        self,
        purchase_order_id: UUID,
        asset_id: UUID,
        session: Session
    ) -> None:
        from app.modules.assets.domain.models import Asset, TechnicalHistory
        from datetime import datetime, timezone
        
        # Validar si ya existe
        asset = session.get(Asset, asset_id)
        if not asset:
            asset = Asset(
                id=asset_id,
                asset_type_id=purchase_order_id, # Fallback/Asociación
                part_number="PN-NEW",
                serial_number=f"SN-{asset_id.hex[:8]}",
                nomenclature="New Component from Purchase",
                condition="SERVICEABLE",
                current_status="IN_STOCK"
            )
            session.add(asset)
            session.flush()

        history = session.get(TechnicalHistory, asset_id)
        if not history:
            history = TechnicalHistory(
                asset_id=asset_id,
                opened_date=datetime.now(timezone.utc).date(),
                current_total_hours=0,
                current_total_cycles=0
            )
            session.add(history)
            session.flush()

    def register_asset(
        self,
        session: Session,
        serial_number: str,
        asset_type_id: UUID,
        organization_id: UUID,
        classification: str,
        part_number: str = "PN-GENERIC",
        nomenclature: str = "Generic Asset"
    ):
        from app.modules.assets.domain.models import Asset, TechnicalHistory
        from app.shared.domain.exceptions import DomainError
        from datetime import date
        from uuid import uuid4

        existing = session.query(Asset).filter_by(serial_number=serial_number).first()
        if existing:
            raise DomainError(f"Asset with serial number {serial_number} already exists.")

        asset = Asset(
            id=uuid4(),
            asset_type_id=asset_type_id,
            part_number=part_number,
            serial_number=serial_number,
            nomenclature=nomenclature,
            classification=classification,
            current_custodian_id=organization_id,
            condition="SERVICEABLE",
            current_status="IN_STOCK"
        )
        session.add(asset)
        session.flush()

        history = TechnicalHistory(
            id=uuid4(),
            asset_id=asset.id,
            opened_date=date.today(),
            current_total_hours=0,
            current_total_cycles=0
        )
        session.add(history)
        session.flush()
        return asset

