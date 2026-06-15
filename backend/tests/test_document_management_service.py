from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.document_management.domain.models import (
    AssetDocumentStatus,
    DocumentType,
    DocumentValidationRule,
    PreservationStatus,
    ServiceCardStatus,
    TechnicalHistoryActionType,
)
from app.modules.document_management.domain.services import DocumentManagementService
from app.shared.domain.exceptions import DomainError


def make_document_type(name: str, mandatory: bool = True) -> DocumentType:
    return DocumentType(id=uuid4(), name=name, description=name, mandatory=mandatory)


def test_create_asset_document_and_append_history_entry_are_audited() -> None:
    service = DocumentManagementService()
    asset_id = uuid4()
    document_type = make_document_type("TECHNICAL_HISTORY")

    document_result = service.create_asset_document(
        asset_id=asset_id,
        document_type=document_type,
        document_code="THC-001",
        version="1",
        issued_date=date.today(),
        expiration_date=None,
        created_by="statistics",
        actor_id="statistics",
    )
    document = document_result.entity
    entry_result = service.append_technical_history_entry(
        asset_document=document,
        entry_date=datetime.now(timezone.utc),
        action_type=TechnicalHistoryActionType.INSTALLED,
        performed_by="maintenance",
        notes="Installed on aircraft.",
        current_hours=Decimal("120.50"),
        current_cycles=44,
        condition_after_action="SERVICEABLE",
        actor_id="maintenance",
    )

    assert document.status == AssetDocumentStatus.ACTIVE
    assert document_result.audit_event.entity_type == "AssetDocument"
    assert entry_result.entity.action_type == TechnicalHistoryActionType.INSTALLED
    assert entry_result.audit_event.entity_type == "TechnicalHistoryEntry"


def test_service_card_and_preservation_record_lifecycle() -> None:
    service = DocumentManagementService()
    asset_id = uuid4()

    card_result = service.issue_service_status_card(
        asset_id=asset_id,
        current_status=ServiceCardStatus.PRESERVED,
        issued_date=date.today(),
        issued_by="pañol",
        notes="Component preserved in storage.",
        actor_id="store",
    )
    preservation_result = service.create_preservation_record(
        asset_id=asset_id,
        preservation_start=date.today(),
        preservation_interval_days=180,
        actor_id="store",
    )
    preservation = preservation_result.entity
    update_result = service.update_preservation_status(
        preservation,
        checked_at=date.today() + timedelta(days=181),
        actor_id="store",
    )

    assert card_result.entity.current_status == ServiceCardStatus.PRESERVED
    assert preservation.status == PreservationStatus.OVERDUE
    assert update_result.audit_event.before_state["status"] == PreservationStatus.ACTIVE


def test_workflow_document_package_links_documents() -> None:
    service = DocumentManagementService()
    asset_id = uuid4()
    technical_history_type = make_document_type("TECHNICAL_HISTORY")
    work_order_type = make_document_type("WORK_ORDER")
    technical_history = service.create_asset_document(
        asset_id,
        technical_history_type,
        "THC-001",
        "1",
        date.today(),
        None,
        "statistics",
        "statistics",
    ).entity
    work_order = service.create_asset_document(
        asset_id,
        work_order_type,
        "WO-001",
        "1",
        date.today(),
        None,
        "pañol",
        "store",
    ).entity

    package, links, audit = service.create_workflow_document_package(
        asset_id=asset_id,
        package_code="PKG-ARS-001",
        created_by="pañol",
        documents=[technical_history, work_order],
        mandatory_document_type_ids={technical_history_type.id, work_order_type.id},
        actor_id="store",
    )

    assert package.package_code == "PKG-ARS-001"
    assert len(links) == 2
    assert all(link.mandatory for link in links)
    assert audit.entity_type == "WorkflowDocumentPackage"


def test_validate_required_documents_blocks_missing_failure_report() -> None:
    service = DocumentManagementService()
    asset_id = uuid4()
    technical_history_type = make_document_type("TECHNICAL_HISTORY")
    failure_report_type = make_document_type("FAILURE_REPORT")
    work_order_type = make_document_type("WORK_ORDER")
    technical_history = service.create_asset_document(
        asset_id,
        technical_history_type,
        "THC-001",
        "1",
        date.today(),
        None,
        "statistics",
        "statistics",
    ).entity
    rules = [
        DocumentValidationRule(id=uuid4(), workflow_type="ARSENAL_TRANSFER", required_document_type_id=technical_history_type.id, mandatory=True),
        DocumentValidationRule(id=uuid4(), workflow_type="ARSENAL_TRANSFER", required_document_type_id=failure_report_type.id, mandatory=True),
        DocumentValidationRule(id=uuid4(), workflow_type="ARSENAL_TRANSFER", required_document_type_id=work_order_type.id, mandatory=True),
    ]

    result = service.validate_required_documents("ARSENAL_TRANSFER", rules, [technical_history])

    assert result.compliant is False
    assert failure_report_type.id in result.missing_document_type_ids
    with pytest.raises(DomainError):
        service.enforce_workflow_documents("ARSENAL_TRANSFER", rules, [technical_history])


def test_compliance_check_and_archive_document() -> None:
    service = DocumentManagementService()
    asset_id = uuid4()
    release_certificate_type = make_document_type("SERVICE_RELEASE_CERTIFICATE")
    release_certificate = service.create_asset_document(
        asset_id,
        release_certificate_type,
        "SRC-001",
        "1",
        date.today(),
        None,
        "quality",
        "quality",
    ).entity
    rules = [
        DocumentValidationRule(
            id=uuid4(),
            workflow_type="SERVICE_RELEASE",
            required_document_type_id=release_certificate_type.id,
            mandatory=True,
        )
    ]

    check_result = service.execute_document_compliance_check(
        asset_id=asset_id,
        workflow_type="SERVICE_RELEASE",
        rules=rules,
        asset_documents=[release_certificate],
        validated_by="quality",
        actor_id="quality",
    )
    archive_result = service.archive_document(release_certificate, actor_id="statistics")

    assert check_result.entity.compliant is True
    assert release_certificate.status == AssetDocumentStatus.ARCHIVED
    assert archive_result.audit_event.before_state["status"] == AssetDocumentStatus.ACTIVE
