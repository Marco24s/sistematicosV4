from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.arsenal_workflow.domain.models import AuditEvent
from app.modules.document_management.domain.models import (
    AssetDocument,
    AssetDocumentStatus,
    DocumentComplianceCheck,
    DocumentType,
    DocumentValidationRule,
    PackageDocumentLink,
    PreservationRecord,
    PreservationStatus,
    ServiceCardStatus,
    ServiceStatusCard,
    TechnicalHistoryActionType,
    TechnicalHistoryEntry,
    WorkflowDocumentPackage,
    WorkflowPackageStatus,
)
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class AuditedResult:
    entity: object
    audit_event: AuditEvent


@dataclass(frozen=True)
class DocumentValidationResult:
    compliant: bool
    missing_document_type_ids: list[UUID]
    failure_reason: str | None


class DocumentManagementService:
    def create_asset_document(
        self,
        asset_id: UUID,
        document_type: DocumentType,
        document_code: str,
        version: str,
        issued_date: date,
        expiration_date: date | None,
        created_by: str,
        actor_id: str,
    ) -> AuditedResult:
        if expiration_date and expiration_date <= issued_date:
            raise DomainError("Document expiration date must be after issued date.")

        document = AssetDocument(
            id=uuid4(),
            asset_id=asset_id,
            document_type_id=document_type.id,
            document_code=document_code,
            version=version,
            issued_date=issued_date,
            expiration_date=expiration_date,
            active=True,
            created_by=created_by,
            status=AssetDocumentStatus.ACTIVE,
        )
        return self._result(document, actor_id, "creo documento tecnico de asset", None, self._asset_document_state(document))

    def append_technical_history_entry(
        self,
        asset_document: AssetDocument,
        entry_date: datetime,
        action_type: TechnicalHistoryActionType,
        performed_by: str,
        notes: str | None,
        current_hours: Decimal,
        current_cycles: int,
        condition_after_action: str,
        actor_id: str,
    ) -> AuditedResult:
        self._assert_active_document(asset_document)
        entry = TechnicalHistoryEntry(
            id=uuid4(),
            asset_document_id=asset_document.id,
            entry_date=entry_date,
            action_type=action_type,
            performed_by=performed_by,
            notes=notes,
            current_hours=current_hours,
            current_cycles=current_cycles,
            condition_after_action=condition_after_action,
        )
        return self._result(entry, actor_id, "agrego entrada al historial tecnico documental", None, self._history_entry_state(entry))

    def issue_service_status_card(
        self,
        asset_id: UUID,
        current_status: ServiceCardStatus,
        issued_date: date,
        issued_by: str,
        notes: str | None,
        actor_id: str,
    ) -> AuditedResult:
        card = ServiceStatusCard(
            id=uuid4(),
            asset_id=asset_id,
            current_status=current_status,
            issued_date=issued_date,
            issued_by=issued_by,
            notes=notes,
            active=True,
        )
        return self._result(card, actor_id, "emitio tarjeta de estado de servicio", None, self._service_card_state(card))

    def create_preservation_record(
        self,
        asset_id: UUID,
        preservation_start: date,
        preservation_interval_days: int,
        actor_id: str,
    ) -> AuditedResult:
        if preservation_interval_days <= 0:
            raise DomainError("Preservation interval must be greater than zero.")
        record = PreservationRecord(
            id=uuid4(),
            asset_id=asset_id,
            preservation_start=preservation_start,
            preservation_interval_days=preservation_interval_days,
            next_preservation_check=preservation_start + timedelta(days=preservation_interval_days),
            last_preservation_check=None,
            status=PreservationStatus.ACTIVE,
        )
        return self._result(record, actor_id, "registro preservado documental", None, self._preservation_state(record))

    def update_preservation_status(
        self,
        record: PreservationRecord,
        checked_at: date,
        actor_id: str,
    ) -> AuditedResult:
        before_state = self._preservation_state(record)
        if checked_at > record.next_preservation_check:
            record.status = PreservationStatus.OVERDUE
        else:
            record.last_preservation_check = checked_at
            record.next_preservation_check = checked_at + timedelta(days=record.preservation_interval_days)
            record.status = PreservationStatus.ACTIVE
        return self._result(record, actor_id, "actualizo estado de preservado", before_state, self._preservation_state(record))

    def create_workflow_document_package(
        self,
        asset_id: UUID,
        package_code: str,
        created_by: str,
        documents: list[AssetDocument],
        mandatory_document_type_ids: set[UUID],
        actor_id: str,
    ) -> tuple[WorkflowDocumentPackage, list[PackageDocumentLink], AuditEvent]:
        package = WorkflowDocumentPackage(
            id=uuid4(),
            asset_id=asset_id,
            package_code=package_code,
            created_by=created_by,
            status=WorkflowPackageStatus.CREATED,
        )
        links = [
            PackageDocumentLink(
                id=uuid4(),
                workflow_package_id=package.id,
                asset_document_id=document.id,
                mandatory=document.document_type_id in mandatory_document_type_ids,
                verified=False,
            )
            for document in documents
        ]
        audit = self._audit_event(
            package,
            actor_id,
            "creo paquete documental de workflow",
            None,
            {"package": self._package_state(package), "document_count": len(links)},
        )
        return package, links, audit

    def validate_required_documents(
        self,
        workflow_type: str,
        rules: list[DocumentValidationRule],
        asset_documents: list[AssetDocument],
        as_of: date | None = None,
    ) -> DocumentValidationResult:
        as_of = as_of or date.today()
        active_type_ids = {
            document.document_type_id
            for document in asset_documents
            if document.active
            and document.status == AssetDocumentStatus.ACTIVE
            and not document.is_deleted
            and (document.expiration_date is None or document.expiration_date >= as_of)
        }
        missing = [
            rule.required_document_type_id
            for rule in rules
            if rule.workflow_type == workflow_type and rule.mandatory and rule.required_document_type_id not in active_type_ids
        ]
        if missing:
            return DocumentValidationResult(
                compliant=False,
                missing_document_type_ids=missing,
                failure_reason=f"Missing mandatory documents for workflow {workflow_type}: {', '.join(str(item) for item in missing)}",
            )
        return DocumentValidationResult(compliant=True, missing_document_type_ids=[], failure_reason=None)

    def archive_document(self, asset_document: AssetDocument, actor_id: str) -> AuditedResult:
        before_state = self._asset_document_state(asset_document)
        asset_document.active = False
        asset_document.status = AssetDocumentStatus.ARCHIVED
        return self._result(asset_document, actor_id, "archivo documento tecnico", before_state, self._asset_document_state(asset_document))

    def execute_document_compliance_check(
        self,
        asset_id: UUID,
        workflow_type: str,
        rules: list[DocumentValidationRule],
        asset_documents: list[AssetDocument],
        validated_by: str,
        actor_id: str,
        validated_at: datetime | None = None,
    ) -> AuditedResult:
        result = self.validate_required_documents(workflow_type, rules, asset_documents, as_of=(validated_at or datetime.now(timezone.utc)).date())
        check = DocumentComplianceCheck(
            id=uuid4(),
            asset_id=asset_id,
            workflow_type=workflow_type,
            validated_at=validated_at or datetime.now(timezone.utc),
            validated_by=validated_by,
            compliant=result.compliant,
            failure_reason=result.failure_reason,
        )
        return self._result(check, actor_id, "ejecuto control de cumplimiento documental", None, self._compliance_check_state(check))

    def enforce_workflow_documents(
        self,
        workflow_type: str,
        rules: list[DocumentValidationRule],
        asset_documents: list[AssetDocument],
    ) -> None:
        result = self.validate_required_documents(workflow_type, rules, asset_documents)
        if not result.compliant:
            raise DomainError(result.failure_reason or "Required workflow documentation is missing.")

    def _assert_active_document(self, document: AssetDocument) -> None:
        if not document.active or document.status != AssetDocumentStatus.ACTIVE:
            raise DomainError("Technical history entries require an active asset document.")

    def _result(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditedResult:
        return AuditedResult(entity=entity, audit_event=self._audit_event(entity, actor_id, action, before_state, after_state))

    def _audit_event(self, entity: object, actor_id: str, action: str, before_state: dict | None, after_state: dict | None) -> AuditEvent:
        return AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            entity_type=type(entity).__name__,
            entity_id=entity.id,
            timestamp=datetime.now(timezone.utc),
            before_state=before_state,
            after_state=after_state,
        )

    def _asset_document_state(self, document: AssetDocument) -> dict:
        return {
            "id": str(document.id),
            "asset_id": str(document.asset_id),
            "document_type_id": str(document.document_type_id),
            "document_code": document.document_code,
            "version": document.version,
            "active": document.active,
            "status": document.status,
        }

    def _history_entry_state(self, entry: TechnicalHistoryEntry) -> dict:
        return {
            "id": str(entry.id),
            "asset_document_id": str(entry.asset_document_id),
            "action_type": entry.action_type,
            "current_hours": str(entry.current_hours),
            "current_cycles": entry.current_cycles,
        }

    def _service_card_state(self, card: ServiceStatusCard) -> dict:
        return {"id": str(card.id), "asset_id": str(card.asset_id), "current_status": card.current_status, "active": card.active}

    def _preservation_state(self, record: PreservationRecord) -> dict:
        return {
            "id": str(record.id),
            "asset_id": str(record.asset_id),
            "next_preservation_check": record.next_preservation_check.isoformat(),
            "status": record.status,
        }

    def _package_state(self, package: WorkflowDocumentPackage) -> dict:
        return {"id": str(package.id), "asset_id": str(package.asset_id), "package_code": package.package_code, "status": package.status}

    def _compliance_check_state(self, check: DocumentComplianceCheck) -> dict:
        return {
            "id": str(check.id),
            "asset_id": str(check.asset_id),
            "workflow_type": check.workflow_type,
            "compliant": check.compliant,
            "failure_reason": check.failure_reason,
        }
