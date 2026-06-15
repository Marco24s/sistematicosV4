from uuid import UUID
from sqlalchemy.orm import Session

class DocumentManagementApplicationService:
    def create_technical_history_entry(
        self,
        asset_id: UUID,
        action_type: str,
        notes: str,
        hours: float,
        cycles: int,
        session: Session
    ) -> None:
        # Importación local para evitar acoplamientos innecesarios a nivel de módulo
        from app.modules.document_management.domain.services import DocumentManagementService
        from app.modules.document_management.domain.models import TechnicalHistoryEntry
        from datetime import datetime
        
        # Obtenemos o creamos una service card si no existe, o registramos la entrada directamente
        entry = TechnicalHistoryEntry(
            asset_document_id=asset_id,  # O ID del documento base asociado
            entry_date=datetime.now().date(),
            action_type=action_type,
            performed_by="SYSTEM_INTEGRATION",
            notes=notes,
            current_hours=hours,
            current_cycles=cycles,
            condition_after_action="SERVICEABLE"
        )
        session.add(entry)
        session.flush()


    def update_service_status(
        self,
        asset_id: UUID,
        status: str,
        session: Session
    ) -> None:
        from app.modules.document_management.domain.models import ServiceStatusCard
        from sqlalchemy import select
        
        stmt = select(ServiceStatusCard).where(ServiceStatusCard.asset_id == asset_id).where(ServiceStatusCard.active == True)
        card = session.scalars(stmt).first()
        if card:
            card.current_status = status
        else:
            new_card = ServiceStatusCard(
                asset_id=asset_id,
                current_status=status,
                active=True,
                notes="Created automatically by integration flow"
            )
            session.add(new_card)
        session.flush()

    def create_workflow_document_package(
        self,
        asset_id: UUID,
        package_code: str,
        session: Session
    ) -> None:
        from app.modules.document_management.domain.models import WorkflowDocumentPackage
        
        package = WorkflowDocumentPackage(
            asset_id=asset_id,
            package_code=package_code,
            created_by="SYSTEM_INTEGRATION",
            status="CREATED"
        )
        session.add(package)
        session.flush()

    def create_service_release_certificate(
        self,
        asset_id: UUID,
        release_id: UUID,
        session: Session
    ) -> None:
        from app.modules.document_management.domain.models import AssetDocument, DocumentType
        from sqlalchemy import select
        
        # Intentamos obtener un tipo de documento para releases
        stmt = select(DocumentType).where(DocumentType.name == "Service Release Certificate")
        doc_type = session.scalars(stmt).first()
        if not doc_type:
            doc_type = DocumentType(name="Service Release Certificate", description="Released component certificate", mandatory=True)
            session.add(doc_type)
            session.flush()

        doc = AssetDocument(
            asset_id=asset_id,
            document_type_id=doc_type.id,
            document_code=f"SRC-{release_id}",
            version=1,
            active=True,
            created_by="SYSTEM_INTEGRATION",
            status="ACTIVE"
        )
        session.add(doc)
        session.flush()
