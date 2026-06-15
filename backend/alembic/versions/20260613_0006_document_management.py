"""document management module

Revision ID: 20260613_0006
Revises: 20260613_0005
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0006"
down_revision: str | None = "20260613_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    document_status = postgresql.ENUM("ACTIVE", "EXPIRED", "ARCHIVED", "CANCELED", name="document_management_asset_document_status", create_type=False)
    history_action = postgresql.ENUM("PURCHASED", "INSTALLED", "REMOVED", "INSPECTED", "REPAIRED", "TRANSFERRED", "SCRAPPED", name="document_management_technical_history_action_type", create_type=False)
    service_card_status = postgresql.ENUM("SERVICEABLE", "UNSERVICEABLE", "IN_REPAIR", "INSPECTION_REQUIRED", "LIMITED_SERVICE", "PRESERVED", name="document_management_service_card_status", create_type=False)
    preservation_status = postgresql.ENUM("ACTIVE", "EXPIRED", "OVERDUE", name="document_management_preservation_status", create_type=False)
    package_status = postgresql.ENUM("CREATED", "IN_TRANSIT", "RECEIVED", "CLOSED", name="document_management_workflow_package_status", create_type=False)

    bind = op.get_bind()
    for enum in (document_status, history_action, service_card_status, preservation_status, package_status):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "document_management_document_types",
        *audit_columns(),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_doc_mgmt_document_types_is_deleted", "document_management_document_types", ["is_deleted"])

    op.create_table(
        "document_management_asset_documents",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_code", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=180), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["document_type_id"], ["document_management_document_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "document_code", "version", name="uq_asset_document_code_version"),
    )
    op.create_index("ix_doc_mgmt_asset_documents_asset_id", "document_management_asset_documents", ["asset_id"])
    op.create_index("ix_doc_mgmt_asset_documents_document_code", "document_management_asset_documents", ["document_code"])
    op.create_index("ix_doc_mgmt_asset_documents_document_type_id", "document_management_asset_documents", ["document_type_id"])
    op.create_index("ix_doc_mgmt_asset_documents_is_deleted", "document_management_asset_documents", ["is_deleted"])

    op.create_table(
        "document_management_technical_history_entries",
        *audit_columns(),
        sa.Column("asset_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action_type", history_action, nullable=False),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("current_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("current_cycles", sa.Integer(), nullable=False),
        sa.Column("condition_after_action", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["asset_document_id"], ["document_management_asset_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doc_mgmt_history_entries_asset_document_id", "document_management_technical_history_entries", ["asset_document_id"])
    op.create_index("ix_doc_mgmt_history_entries_is_deleted", "document_management_technical_history_entries", ["is_deleted"])

    op.create_table(
        "document_management_service_status_cards",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_status", service_card_status, nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=False),
        sa.Column("issued_by", sa.String(length=180), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doc_mgmt_service_cards_asset_id", "document_management_service_status_cards", ["asset_id"])
    op.create_index("ix_doc_mgmt_service_cards_is_deleted", "document_management_service_status_cards", ["is_deleted"])

    op.create_table(
        "document_management_preservation_records",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preservation_start", sa.Date(), nullable=False),
        sa.Column("preservation_interval_days", sa.Integer(), nullable=False),
        sa.Column("next_preservation_check", sa.Date(), nullable=False),
        sa.Column("last_preservation_check", sa.Date(), nullable=True),
        sa.Column("status", preservation_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doc_mgmt_preservation_asset_id", "document_management_preservation_records", ["asset_id"])
    op.create_index("ix_doc_mgmt_preservation_is_deleted", "document_management_preservation_records", ["is_deleted"])

    op.create_table(
        "document_management_workflow_packages",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_code", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.String(length=180), nullable=False),
        sa.Column("status", package_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_code"),
    )
    op.create_index("ix_doc_mgmt_workflow_packages_asset_id", "document_management_workflow_packages", ["asset_id"])
    op.create_index("ix_doc_mgmt_workflow_packages_is_deleted", "document_management_workflow_packages", ["is_deleted"])

    op.create_table(
        "document_management_package_document_links",
        *audit_columns(),
        sa.Column("workflow_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["asset_document_id"], ["document_management_asset_documents.id"]),
        sa.ForeignKeyConstraint(["workflow_package_id"], ["document_management_workflow_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_package_id", "asset_document_id", name="uq_package_document_link"),
    )
    op.create_index("ix_doc_mgmt_package_links_asset_document_id", "document_management_package_document_links", ["asset_document_id"])
    op.create_index("ix_doc_mgmt_package_links_is_deleted", "document_management_package_document_links", ["is_deleted"])
    op.create_index("ix_doc_mgmt_package_links_workflow_package_id", "document_management_package_document_links", ["workflow_package_id"])

    op.create_table(
        "document_management_validation_rules",
        *audit_columns(),
        sa.Column("workflow_type", sa.String(length=120), nullable=False),
        sa.Column("required_document_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["required_document_type_id"], ["document_management_document_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_type", "required_document_type_id", name="uq_document_validation_rule"),
    )
    op.create_index("ix_doc_mgmt_validation_rules_doc_type_id", "document_management_validation_rules", ["required_document_type_id"])
    op.create_index("ix_doc_mgmt_validation_rules_is_deleted", "document_management_validation_rules", ["is_deleted"])
    op.create_index("ix_doc_mgmt_validation_rules_workflow_type", "document_management_validation_rules", ["workflow_type"])

    op.create_table(
        "document_management_compliance_checks",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_type", sa.String(length=120), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validated_by", sa.String(length=180), nullable=False),
        sa.Column("compliant", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doc_mgmt_compliance_checks_asset_id", "document_management_compliance_checks", ["asset_id"])
    op.create_index("ix_doc_mgmt_compliance_checks_is_deleted", "document_management_compliance_checks", ["is_deleted"])
    op.create_index("ix_doc_mgmt_compliance_checks_workflow_type", "document_management_compliance_checks", ["workflow_type"])


def downgrade() -> None:
    op.drop_index("ix_doc_mgmt_compliance_checks_workflow_type", table_name="document_management_compliance_checks")
    op.drop_index("ix_doc_mgmt_compliance_checks_is_deleted", table_name="document_management_compliance_checks")
    op.drop_index("ix_doc_mgmt_compliance_checks_asset_id", table_name="document_management_compliance_checks")
    op.drop_table("document_management_compliance_checks")
    op.drop_index("ix_doc_mgmt_validation_rules_workflow_type", table_name="document_management_validation_rules")
    op.drop_index("ix_doc_mgmt_validation_rules_is_deleted", table_name="document_management_validation_rules")
    op.drop_index("ix_doc_mgmt_validation_rules_doc_type_id", table_name="document_management_validation_rules")
    op.drop_table("document_management_validation_rules")
    op.drop_index("ix_doc_mgmt_package_links_workflow_package_id", table_name="document_management_package_document_links")
    op.drop_index("ix_doc_mgmt_package_links_is_deleted", table_name="document_management_package_document_links")
    op.drop_index("ix_doc_mgmt_package_links_asset_document_id", table_name="document_management_package_document_links")
    op.drop_table("document_management_package_document_links")
    op.drop_index("ix_doc_mgmt_workflow_packages_is_deleted", table_name="document_management_workflow_packages")
    op.drop_index("ix_doc_mgmt_workflow_packages_asset_id", table_name="document_management_workflow_packages")
    op.drop_table("document_management_workflow_packages")
    op.drop_index("ix_doc_mgmt_preservation_is_deleted", table_name="document_management_preservation_records")
    op.drop_index("ix_doc_mgmt_preservation_asset_id", table_name="document_management_preservation_records")
    op.drop_table("document_management_preservation_records")
    op.drop_index("ix_doc_mgmt_service_cards_is_deleted", table_name="document_management_service_status_cards")
    op.drop_index("ix_doc_mgmt_service_cards_asset_id", table_name="document_management_service_status_cards")
    op.drop_table("document_management_service_status_cards")
    op.drop_index("ix_doc_mgmt_history_entries_is_deleted", table_name="document_management_technical_history_entries")
    op.drop_index("ix_doc_mgmt_history_entries_asset_document_id", table_name="document_management_technical_history_entries")
    op.drop_table("document_management_technical_history_entries")
    op.drop_index("ix_doc_mgmt_asset_documents_is_deleted", table_name="document_management_asset_documents")
    op.drop_index("ix_doc_mgmt_asset_documents_document_type_id", table_name="document_management_asset_documents")
    op.drop_index("ix_doc_mgmt_asset_documents_document_code", table_name="document_management_asset_documents")
    op.drop_index("ix_doc_mgmt_asset_documents_asset_id", table_name="document_management_asset_documents")
    op.drop_table("document_management_asset_documents")
    op.drop_index("ix_doc_mgmt_document_types_is_deleted", table_name="document_management_document_types")
    op.drop_table("document_management_document_types")

    bind = op.get_bind()
    for enum_name in (
        "document_management_workflow_package_status",
        "document_management_preservation_status",
        "document_management_service_card_status",
        "document_management_technical_history_action_type",
        "document_management_asset_document_status",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
