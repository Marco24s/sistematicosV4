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
        user_id: UUID,
        origin_terminal: str,
        serial_number: str,
        asset_type_id: UUID,
        organization_id: UUID,
        classification: str,
        part_number: str = "PN-GENERIC",
        nomenclature: str = "Generic Asset"
    ):
        from app.modules.assets.domain.models import Asset, TechnicalHistory, AssetType
        from app.modules.auditing.application.services import log_audit_event
        from app.modules.document_management.domain.models import AssetDocument, DocumentType
        from app.shared.domain.exceptions import DomainError
        from datetime import date
        from uuid import uuid4

        existing = session.query(Asset).filter_by(serial_number=serial_number).first()
        if existing:
            raise DomainError(f"Asset with serial number {serial_number} already exists.")

        asset_type = session.get(AssetType, asset_type_id)
        if not asset_type:
            raise DomainError(f"AssetType {asset_type_id} does not exist.")

        # Commissioning Workflow: Todo asset nace en PENDING_COMMISSIONING y QUARANTINED
        asset = Asset(
            id=uuid4(),
            asset_type_id=asset_type_id,
            part_number=part_number,
            serial_number=serial_number,
            nomenclature=nomenclature,
            classification=classification,
            organization_owner_id=organization_id,
            current_custodian_id=None,
            condition="QUARANTINED",
            current_status="PENDING_COMMISSIONING"
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

        # Aircraft Specific Logic
        if asset_type.category == "AIRCRAFT":
            from app.modules.configuration_baseline.domain.models import AircraftBaselineConfiguration
            # 1. Configuration Baseline
            baseline = AircraftBaselineConfiguration(
                id=uuid4(),
                aircraft_model_id=asset.asset_type_id,
                approved_configuration_json={"status": "INITIAL_DELIVERY"},
                approved_by_engineering="SYSTEM_AUTO",
                revision_number="1.0.0",
                certification_date=date.today()
            )
            session.add(baseline)
            
            # 2. Documentos Inmutables Requeridos
            doc_types = [
                "Historical Record Book",
                "Initial Configuration Snapshot",
                "Initial Technical Acceptance Record"
            ]
            for doc_name in doc_types:
                # Nos aseguramos de tener el DocumentType
                dtype = session.query(DocumentType).filter_by(name=doc_name).first()
                if not dtype:
                    dtype = DocumentType(id=uuid4(), name=doc_name, description=doc_name)
                    session.add(dtype)
                    session.flush()
                
                code_prefix = "".join(word[0] for word in doc_name.split()).upper()
                doc = AssetDocument(
                    id=uuid4(),
                    asset_id=asset.id,
                    document_type_id=dtype.id,
                    document_code=f"{code_prefix}-{asset.serial_number}",
                    version="1.0",
                    issued_date=date.today(),
                    active=True,
                    created_by="SYSTEM_COMMISSIONING",
                    status="ACTIVE"
                )
                session.add(doc)
            session.flush()

        # Caja Negra: Auditoría
        log_audit_event(
            db=session,
            user_id=user_id,
            action="ASSET_REGISTERED",
            entity_type="Asset",
            entity_id=asset.id,
            origin_terminal=origin_terminal,
            document_reference=None,
            old_state=None,
            new_state={
                "serial_number": asset.serial_number,
                "condition": asset.condition,
                "status": asset.current_status,
                "classification": asset.classification
            },
            reason="Initial Asset Commissioning"
        )

        return asset

