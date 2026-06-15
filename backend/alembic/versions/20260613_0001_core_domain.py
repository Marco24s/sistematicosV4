"""core domain model

Revision ID: 20260613_0001
Revises:
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0001"
down_revision: str | None = None
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
    organization_type = postgresql.ENUM("SQUADRON", "ARSENAL", name="organization_type", create_type=False)
    department_type = postgresql.ENUM(
        "OPERATIONS",
        "LOGISTICS",
        "MAINTENANCE",
        "QUALITY",
        "STATISTICS",
        "AERONAUTICAL_STORES",
        "PROCUREMENT",
        "ENGINEERING",
        "SUPPORT",
        "ACCESSORIES",
        "HYDRAULICS",
        "ENGINES",
        "DYNAMIC_COMPONENTS",
        "ELECTRICAL_ACCESSORIES",
        name="department_type",
        create_type=False,
    )
    asset_condition = postgresql.ENUM(
        "SERVICEABLE",
        "UNSERVICEABLE",
        "REPAIRABLE",
        "QUARANTINED",
        "PRESERVED",
        "CONDEMNED",
        name="asset_condition",
        create_type=False,
    )
    asset_status = postgresql.ENUM(
        "IN_STOCK",
        "INSTALLED",
        "IN_TRANSFER",
        "IN_REPAIR",
        "WAITING_QUALITY",
        "RELEASED",
        "GROUNDED",
        "SCRAPPED",
        name="asset_status",
        create_type=False,
    )
    transfer_status = postgresql.ENUM(
        "CREATED",
        "IN_TRANSIT",
        "RECEIVED",
        "CANCELLED",
        name="transfer_status",
        create_type=False,
    )
    maintenance_interval_type = postgresql.ENUM(
        "FLIGHT_HOURS",
        "CALENDAR_DAYS",
        "CYCLES",
        name="maintenance_interval_type",
        create_type=False,
    )
    failure_severity = postgresql.ENUM(
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "FLIGHT_SAFETY",
        name="failure_severity",
        create_type=False,
    )
    work_order_priority = postgresql.ENUM(
        "ROUTINE",
        "URGENT",
        "AOG",
        "FLIGHT_SAFETY",
        name="work_order_priority",
        create_type=False,
    )
    work_order_status = postgresql.ENUM(
        "CREATED",
        "IN_TRANSIT",
        "RECEIVED",
        "UNDER_ENGINEERING_REVIEW",
        "IN_REPAIR",
        "WAITING_QUALITY",
        "COMPLETED",
        name="work_order_status",
        create_type=False,
    )

    bind = op.get_bind()
    for enum in (
        organization_type,
        department_type,
        asset_condition,
        asset_status,
        transfer_status,
        maintenance_interval_type,
        failure_severity,
        work_order_priority,
        work_order_status,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        *audit_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("organization_type", organization_type, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_organizations_is_deleted", "organizations", ["is_deleted"])

    op.create_table(
        "asset_types",
        *audit_columns(),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "category", name="uq_asset_types_name_category"),
    )
    op.create_index("ix_asset_types_category", "asset_types", ["category"])
    op.create_index("ix_asset_types_is_deleted", "asset_types", ["is_deleted"])

    op.create_table(
        "maintenance_programs",
        *audit_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("interval_type", maintenance_interval_type, nullable=False),
        sa.Column("interval_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "interval_type", "interval_value", name="uq_maintenance_programs_rule"),
    )
    op.create_index("ix_maintenance_programs_is_deleted", "maintenance_programs", ["is_deleted"])

    op.create_table(
        "departments",
        *audit_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("department_type", department_type, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_departments_organization_name"),
    )
    op.create_index("ix_departments_is_deleted", "departments", ["is_deleted"])
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"])

    op.create_table(
        "assets",
        *audit_columns(),
        sa.Column("asset_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("part_number", sa.String(length=120), nullable=False),
        sa.Column("serial_number", sa.String(length=120), nullable=False),
        sa.Column("nomenclature", sa.String(length=240), nullable=False),
        sa.Column("condition", asset_condition, nullable=False),
        sa.Column("current_status", asset_status, nullable=False),
        sa.Column("current_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"]),
        sa.ForeignKeyConstraint(["current_custodian_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
    )
    op.create_index("ix_assets_asset_type_id", "assets", ["asset_type_id"])
    op.create_index("ix_assets_current_custodian_id", "assets", ["current_custodian_id"])
    op.create_index("ix_assets_is_deleted", "assets", ["is_deleted"])
    op.create_index("ix_assets_part_number", "assets", ["part_number"])
    op.create_index("ix_assets_serial_number", "assets", ["serial_number"])

    op.create_table(
        "technical_histories",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opened_date", sa.Date(), nullable=False),
        sa.Column("current_total_hours", sa.Integer(), nullable=False),
        sa.Column("current_total_cycles", sa.Integer(), nullable=False),
        sa.Column("calendar_expiration", sa.Date(), nullable=True),
        sa.Column("preservation_expiration", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
    )
    op.create_index("ix_technical_histories_asset_id", "technical_histories", ["asset_id"])
    op.create_index("ix_technical_histories_is_deleted", "technical_histories", ["is_deleted"])

    op.create_table(
        "asset_transfers",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("origin_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", transfer_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["origin_department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["destination_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_transfers_asset_id", "asset_transfers", ["asset_id"])
    op.create_index("ix_asset_transfers_destination_department_id", "asset_transfers", ["destination_department_id"])
    op.create_index("ix_asset_transfers_is_deleted", "asset_transfers", ["is_deleted"])
    op.create_index("ix_asset_transfers_origin_department_id", "asset_transfers", ["origin_department_id"])

    op.create_table(
        "maintenance_counters",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_usage", sa.Integer(), nullable=False),
        sa.Column("remaining_usage", sa.Integer(), nullable=False),
        sa.Column("next_due", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["maintenance_program_id"], ["maintenance_programs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "maintenance_program_id", name="uq_counter_asset_program"),
    )
    op.create_index("ix_maintenance_counters_asset_id", "maintenance_counters", ["asset_id"])
    op.create_index("ix_maintenance_counters_is_deleted", "maintenance_counters", ["is_deleted"])
    op.create_index("ix_maintenance_counters_maintenance_program_id", "maintenance_counters", ["maintenance_program_id"])

    op.create_table(
        "failure_reports",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reported_by", sa.String(length=180), nullable=False),
        sa.Column("failure_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", failure_severity, nullable=False),
        sa.Column("aircraft_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["aircraft_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_failure_reports_aircraft_id", "failure_reports", ["aircraft_id"])
    op.create_index("ix_failure_reports_asset_id", "failure_reports", ["asset_id"])
    op.create_index("ix_failure_reports_is_deleted", "failure_reports", ["is_deleted"])

    op.create_table(
        "work_orders",
        *audit_columns(),
        sa.Column("failure_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("origin_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("priority", work_order_priority, nullable=False),
        sa.Column("status", work_order_status, nullable=False),
        sa.ForeignKeyConstraint(["assigned_department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["failure_report_id"], ["failure_reports.id"]),
        sa.ForeignKeyConstraint(["origin_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_orders_assigned_department_id", "work_orders", ["assigned_department_id"])
    op.create_index("ix_work_orders_failure_report_id", "work_orders", ["failure_report_id"])
    op.create_index("ix_work_orders_is_deleted", "work_orders", ["is_deleted"])
    op.create_index("ix_work_orders_origin_department_id", "work_orders", ["origin_department_id"])


def downgrade() -> None:
    op.drop_index("ix_work_orders_origin_department_id", table_name="work_orders")
    op.drop_index("ix_work_orders_is_deleted", table_name="work_orders")
    op.drop_index("ix_work_orders_failure_report_id", table_name="work_orders")
    op.drop_index("ix_work_orders_assigned_department_id", table_name="work_orders")
    op.drop_table("work_orders")
    op.drop_index("ix_failure_reports_is_deleted", table_name="failure_reports")
    op.drop_index("ix_failure_reports_asset_id", table_name="failure_reports")
    op.drop_index("ix_failure_reports_aircraft_id", table_name="failure_reports")
    op.drop_table("failure_reports")
    op.drop_index("ix_maintenance_counters_maintenance_program_id", table_name="maintenance_counters")
    op.drop_index("ix_maintenance_counters_is_deleted", table_name="maintenance_counters")
    op.drop_index("ix_maintenance_counters_asset_id", table_name="maintenance_counters")
    op.drop_table("maintenance_counters")
    op.drop_index("ix_asset_transfers_origin_department_id", table_name="asset_transfers")
    op.drop_index("ix_asset_transfers_is_deleted", table_name="asset_transfers")
    op.drop_index("ix_asset_transfers_destination_department_id", table_name="asset_transfers")
    op.drop_index("ix_asset_transfers_asset_id", table_name="asset_transfers")
    op.drop_table("asset_transfers")
    op.drop_index("ix_technical_histories_is_deleted", table_name="technical_histories")
    op.drop_index("ix_technical_histories_asset_id", table_name="technical_histories")
    op.drop_table("technical_histories")
    op.drop_index("ix_assets_serial_number", table_name="assets")
    op.drop_index("ix_assets_part_number", table_name="assets")
    op.drop_index("ix_assets_is_deleted", table_name="assets")
    op.drop_index("ix_assets_current_custodian_id", table_name="assets")
    op.drop_index("ix_assets_asset_type_id", table_name="assets")
    op.drop_table("assets")
    op.drop_index("ix_departments_organization_id", table_name="departments")
    op.drop_index("ix_departments_is_deleted", table_name="departments")
    op.drop_table("departments")
    op.drop_index("ix_maintenance_programs_is_deleted", table_name="maintenance_programs")
    op.drop_table("maintenance_programs")
    op.drop_index("ix_asset_types_is_deleted", table_name="asset_types")
    op.drop_index("ix_asset_types_category", table_name="asset_types")
    op.drop_table("asset_types")
    op.drop_index("ix_organizations_is_deleted", table_name="organizations")
    op.drop_table("organizations")

    bind = op.get_bind()
    for enum_name in (
        "work_order_status",
        "work_order_priority",
        "failure_severity",
        "maintenance_interval_type",
        "transfer_status",
        "asset_status",
        "asset_condition",
        "department_type",
        "organization_type",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
