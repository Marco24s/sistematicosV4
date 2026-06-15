"""squadron operations module

Revision ID: 20260613_0004
Revises: 20260613_0003
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0004"
down_revision: str | None = "20260613_0003"
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
    mounted_status = postgresql.ENUM("ACTIVE", "REMOVED", name="squadron_mounted_component_status", create_type=False)
    inspection_interval_type = postgresql.ENUM("FLIGHT_HOURS", "CALENDAR_DAYS", name="squadron_aircraft_inspection_interval_type", create_type=False)
    inspection_status = postgresql.ENUM("ACTIVE", "OVERDUE", "COMPLETED", name="squadron_aircraft_inspection_status", create_type=False)
    statistical_status = postgresql.ENUM("NORMAL", "WARNING", "OVERDUE", "GROUNDING_REQUIRED", name="squadron_statistical_control_status", create_type=False)
    maintenance_action_status = postgresql.ENUM("PENDING", "COMPLETED", "WAITING_QUALITY", name="squadron_maintenance_action_status", create_type=False)
    quality_status = postgresql.ENUM("APPROVED", "REJECTED", name="squadron_quality_approval_status", create_type=False)
    inventory_movement_type = postgresql.ENUM(
        "RECEIVED_FROM_ARSENAL",
        "DELIVERED_FOR_INSTALLATION",
        "RECEIVED_AFTER_REMOVAL",
        "PREPARED_FOR_ARSENAL_TRANSFER",
        name="squadron_inventory_movement_type",
        create_type=False,
    )
    block_severity = postgresql.ENUM("WARNING", "CRITICAL", "GROUNDING", name="squadron_airworthiness_block_severity", create_type=False)

    bind = op.get_bind()
    for enum in (
        mounted_status,
        inspection_interval_type,
        inspection_status,
        statistical_status,
        maintenance_action_status,
        quality_status,
        inventory_movement_type,
        block_severity,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "squadron_aircraft_configurations",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("configuration_name", sa.String(length=180), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_aircraft_configurations_aircraft_asset_id", "squadron_aircraft_configurations", ["aircraft_asset_id"])
    op.create_index("ix_squadron_aircraft_configurations_is_deleted", "squadron_aircraft_configurations", ["is_deleted"])

    op.create_table(
        "squadron_mounted_components",
        *audit_columns(),
        sa.Column("aircraft_configuration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_code", sa.String(length=80), nullable=False),
        sa.Column("installation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("installed_by", sa.String(length=180), nullable=False),
        sa.Column("status", mounted_status, nullable=False),
        sa.ForeignKeyConstraint(["aircraft_configuration_id"], ["squadron_aircraft_configurations.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_mounted_components_aircraft_configuration_id", "squadron_mounted_components", ["aircraft_configuration_id"])
    op.create_index("ix_squadron_mounted_components_asset_id", "squadron_mounted_components", ["asset_id"])
    op.create_index("ix_squadron_mounted_components_is_deleted", "squadron_mounted_components", ["is_deleted"])

    op.create_table(
        "squadron_aircraft_inspection_programs",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspection_name", sa.String(length=180), nullable=False),
        sa.Column("interval_type", inspection_interval_type, nullable=False),
        sa.Column("interval_value", sa.Integer(), nullable=False),
        sa.Column("last_performed", sa.Date(), nullable=True),
        sa.Column("next_due", sa.Date(), nullable=True),
        sa.Column("status", inspection_status, nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_aircraft_inspection_programs_aircraft_asset_id", "squadron_aircraft_inspection_programs", ["aircraft_asset_id"])
    op.create_index("ix_squadron_aircraft_inspection_programs_is_deleted", "squadron_aircraft_inspection_programs", ["is_deleted"])

    op.create_table(
        "squadron_statistical_control_records",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("remaining_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_cycles", sa.Integer(), nullable=False),
        sa.Column("remaining_cycles", sa.Integer(), nullable=True),
        sa.Column("calendar_expiration", sa.Date(), nullable=True),
        sa.Column("next_inspection_due", sa.Date(), nullable=True),
        sa.Column("status", statistical_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
    )
    op.create_index("ix_squadron_statistical_control_records_asset_id", "squadron_statistical_control_records", ["asset_id"])
    op.create_index("ix_squadron_statistical_control_records_is_deleted", "squadron_statistical_control_records", ["is_deleted"])

    op.create_table(
        "squadron_maintenance_actions",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("action_type", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requires_quality_approval", sa.Boolean(), nullable=False),
        sa.Column("status", maintenance_action_status, nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_maintenance_actions_aircraft_asset_id", "squadron_maintenance_actions", ["aircraft_asset_id"])
    op.create_index("ix_squadron_maintenance_actions_is_deleted", "squadron_maintenance_actions", ["is_deleted"])

    op.create_table(
        "squadron_quality_approvals",
        *audit_columns(),
        sa.Column("maintenance_action_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspector_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", quality_status, nullable=False),
        sa.ForeignKeyConstraint(["maintenance_action_id"], ["squadron_maintenance_actions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_quality_approvals_inspector_id", "squadron_quality_approvals", ["inspector_id"])
    op.create_index("ix_squadron_quality_approvals_is_deleted", "squadron_quality_approvals", ["is_deleted"])
    op.create_index("ix_squadron_quality_approvals_maintenance_action_id", "squadron_quality_approvals", ["maintenance_action_id"])

    op.create_table(
        "squadron_inventory_movements",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", inventory_movement_type, nullable=False),
        sa.Column("origin_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("movement_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["destination_department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["origin_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_inventory_movements_asset_id", "squadron_inventory_movements", ["asset_id"])
    op.create_index("ix_squadron_inventory_movements_destination_department_id", "squadron_inventory_movements", ["destination_department_id"])
    op.create_index("ix_squadron_inventory_movements_is_deleted", "squadron_inventory_movements", ["is_deleted"])
    op.create_index("ix_squadron_inventory_movements_origin_department_id", "squadron_inventory_movements", ["origin_department_id"])

    op.create_table(
        "squadron_airworthiness_blocks",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("blocked_since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", block_severity, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_squadron_airworthiness_blocks_aircraft_asset_id", "squadron_airworthiness_blocks", ["aircraft_asset_id"])
    op.create_index("ix_squadron_airworthiness_blocks_is_deleted", "squadron_airworthiness_blocks", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_squadron_airworthiness_blocks_is_deleted", table_name="squadron_airworthiness_blocks")
    op.drop_index("ix_squadron_airworthiness_blocks_aircraft_asset_id", table_name="squadron_airworthiness_blocks")
    op.drop_table("squadron_airworthiness_blocks")
    op.drop_index("ix_squadron_inventory_movements_origin_department_id", table_name="squadron_inventory_movements")
    op.drop_index("ix_squadron_inventory_movements_is_deleted", table_name="squadron_inventory_movements")
    op.drop_index("ix_squadron_inventory_movements_destination_department_id", table_name="squadron_inventory_movements")
    op.drop_index("ix_squadron_inventory_movements_asset_id", table_name="squadron_inventory_movements")
    op.drop_table("squadron_inventory_movements")
    op.drop_index("ix_squadron_quality_approvals_maintenance_action_id", table_name="squadron_quality_approvals")
    op.drop_index("ix_squadron_quality_approvals_is_deleted", table_name="squadron_quality_approvals")
    op.drop_index("ix_squadron_quality_approvals_inspector_id", table_name="squadron_quality_approvals")
    op.drop_table("squadron_quality_approvals")
    op.drop_index("ix_squadron_maintenance_actions_is_deleted", table_name="squadron_maintenance_actions")
    op.drop_index("ix_squadron_maintenance_actions_aircraft_asset_id", table_name="squadron_maintenance_actions")
    op.drop_table("squadron_maintenance_actions")
    op.drop_index("ix_squadron_statistical_control_records_is_deleted", table_name="squadron_statistical_control_records")
    op.drop_index("ix_squadron_statistical_control_records_asset_id", table_name="squadron_statistical_control_records")
    op.drop_table("squadron_statistical_control_records")
    op.drop_index("ix_squadron_aircraft_inspection_programs_is_deleted", table_name="squadron_aircraft_inspection_programs")
    op.drop_index("ix_squadron_aircraft_inspection_programs_aircraft_asset_id", table_name="squadron_aircraft_inspection_programs")
    op.drop_table("squadron_aircraft_inspection_programs")
    op.drop_index("ix_squadron_mounted_components_is_deleted", table_name="squadron_mounted_components")
    op.drop_index("ix_squadron_mounted_components_asset_id", table_name="squadron_mounted_components")
    op.drop_index("ix_squadron_mounted_components_aircraft_configuration_id", table_name="squadron_mounted_components")
    op.drop_table("squadron_mounted_components")
    op.drop_index("ix_squadron_aircraft_configurations_is_deleted", table_name="squadron_aircraft_configurations")
    op.drop_index("ix_squadron_aircraft_configurations_aircraft_asset_id", table_name="squadron_aircraft_configurations")
    op.drop_table("squadron_aircraft_configurations")

    bind = op.get_bind()
    for enum_name in (
        "squadron_airworthiness_block_severity",
        "squadron_inventory_movement_type",
        "squadron_quality_approval_status",
        "squadron_maintenance_action_status",
        "squadron_statistical_control_status",
        "squadron_aircraft_inspection_status",
        "squadron_aircraft_inspection_interval_type",
        "squadron_mounted_component_status",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
