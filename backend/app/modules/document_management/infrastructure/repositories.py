from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.document_management.domain.models import (
    AssetDocument,
    AssetDocumentStatus,
    DocumentComplianceCheck,
    DocumentType,
    DocumentValidationRule,
    PackageDocumentLink,
    PreservationRecord,
    ServiceStatusCard,
    TechnicalHistoryEntry,
    WorkflowDocumentPackage,
)
from app.shared.infrastructure.repositories import BaseRepository


class DocumentTypeRepository(BaseRepository[DocumentType]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, DocumentType)


class AssetDocumentRepository(BaseRepository[AssetDocument]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AssetDocument)

    def list_active_by_asset_id(self, asset_id: UUID) -> list[AssetDocument]:
        statement = select(AssetDocument).where(
            AssetDocument.asset_id == asset_id,
            AssetDocument.active.is_(True),
            AssetDocument.status == AssetDocumentStatus.ACTIVE,
            AssetDocument.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class TechnicalHistoryEntryRepository(BaseRepository[TechnicalHistoryEntry]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicalHistoryEntry)


class ServiceStatusCardRepository(BaseRepository[ServiceStatusCard]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ServiceStatusCard)


class PreservationRecordRepository(BaseRepository[PreservationRecord]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, PreservationRecord)


class WorkflowDocumentPackageRepository(BaseRepository[WorkflowDocumentPackage]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, WorkflowDocumentPackage)


class PackageDocumentLinkRepository(BaseRepository[PackageDocumentLink]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, PackageDocumentLink)


class DocumentValidationRuleRepository(BaseRepository[DocumentValidationRule]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, DocumentValidationRule)

    def list_by_workflow_type(self, workflow_type: str) -> list[DocumentValidationRule]:
        statement = select(DocumentValidationRule).where(
            DocumentValidationRule.workflow_type == workflow_type,
            DocumentValidationRule.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class DocumentComplianceCheckRepository(BaseRepository[DocumentComplianceCheck]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, DocumentComplianceCheck)
