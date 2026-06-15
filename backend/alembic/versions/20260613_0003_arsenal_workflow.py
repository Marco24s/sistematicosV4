"""arsenal workflow module

Revision ID: 20260613_0003
Revises: 20260613_0002
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0003"
down_revision: str | None = "20260613_0002"
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
    request_status = postgresql.ENUM(
        "CREATED",
        "READY_FOR_TRANSFER",
        "IN_TRANSIT",
        "RECEIVED_BY_ARSENAL",
        "ASSIGNED_TO_SECTION",
        "UNDER_ENGINEERING_REVIEW",
        "WAITING_REPAIR",
        "UNDER_REPAIR",
        "WAITING_QUALITY",
        "COMPLETED",
        "REJECTED",
        name="arsenal_maintenance_request_status",
        create_type=False,
    )
    request_priority = postgresql.ENUM("CRITICAL", "HIGH", "NORMAL", "LOW", name="arsenal_maintenance_request_priority", create_type=False)
    section_priority = postgresql.ENUM("CRITICAL", "HIGH", "NORMAL", "LOW", name="arsenal_section_assignment_priority", create_type=False)
    reception_status = postgresql.ENUM("PENDING_REVIEW", "RECEIVED", "REJECTED", name="arsenal_component_reception_status", create_type=False)
    assignment_status = postgresql.ENUM("PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", name="arsenal_section_assignment_status", create_type=False)
    review_status = postgresql.ENUM("PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", name="arsenal_engineering_review_status", create_type=False)
    repair_status = postgresql.ENUM("WAITING", "IN_PROGRESS", "COMPLETED", "FAILED", name="arsenal_repair_task_status", create_type=False)
    inspection_status = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", name="arsenal_quality_inspection_status", create_type=False)
    release_status = postgresql.ENUM("SERVICEABLE", "LIMITED_SERVICE", "UNSERVICEABLE", name="arsenal_service_release_status", create_type=False)

    bind = op.get_bind()
    for enum in (
        request_status,
        request_priority,
        section_priority,
        reception_status,
        assignment_status,
        review_status,
        repair_status,
        inspection_status,
        release_status,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "arsenal_maintenance_requests",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("origin_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("priority", request_priority, nullable=False),
        sa.Column("failure_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", sa.String(length=180), nullable=False),
        sa.Column("status", request_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["failure_report_id"], ["failure_reports.id"]),
        sa.ForeignKeyConstraint(["origin_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_maintenance_requests_asset_id", "arsenal_maintenance_requests", ["asset_id"])
    op.create_index("ix_arsenal_maintenance_requests_failure_report_id", "arsenal_maintenance_requests", ["failure_report_id"])
    op.create_index("ix_arsenal_maintenance_requests_is_deleted", "arsenal_maintenance_requests", ["is_deleted"])
    op.create_index("ix_arsenal_maintenance_requests_origin_department_id", "arsenal_maintenance_requests", ["origin_department_id"])

    op.create_table(
        "arsenal_component_receptions",
        *audit_columns(),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("received_by_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("condition_notes", sa.Text(), nullable=True),
        sa.Column("documentation_complete", sa.Boolean(), nullable=False),
        sa.Column("status", reception_status, nullable=False),
        sa.ForeignKeyConstraint(["maintenance_request_id"], ["arsenal_maintenance_requests.id"]),
        sa.ForeignKeyConstraint(["received_by_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_component_receptions_is_deleted", "arsenal_component_receptions", ["is_deleted"])
    op.create_index("ix_arsenal_component_receptions_maintenance_request_id", "arsenal_component_receptions", ["maintenance_request_id"])
    op.create_index("ix_arsenal_component_receptions_received_by_department_id", "arsenal_component_receptions", ["received_by_department_id"])

    op.create_table(
        "arsenal_section_assignments",
        *audit_columns(),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", sa.String(length=180), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("priority", section_priority, nullable=False),
        sa.Column("status", assignment_status, nullable=False),
        sa.ForeignKeyConstraint(["assigned_section_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["maintenance_request_id"], ["arsenal_maintenance_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_section_assignments_assigned_section_id", "arsenal_section_assignments", ["assigned_section_id"])
    op.create_index("ix_arsenal_section_assignments_is_deleted", "arsenal_section_assignments", ["is_deleted"])
    op.create_index("ix_arsenal_section_assignments_maintenance_request_id", "arsenal_section_assignments", ["maintenance_request_id"])

    op.create_table(
        "arsenal_engineering_reviews",
        *audit_columns(),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engineer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_analysis", sa.Text(), nullable=False),
        sa.Column("repairable", sa.Boolean(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("status", review_status, nullable=False),
        sa.ForeignKeyConstraint(["maintenance_request_id"], ["arsenal_maintenance_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_engineering_reviews_engineer_id", "arsenal_engineering_reviews", ["engineer_id"])
    op.create_index("ix_arsenal_engineering_reviews_is_deleted", "arsenal_engineering_reviews", ["is_deleted"])
    op.create_index("ix_arsenal_engineering_reviews_maintenance_request_id", "arsenal_engineering_reviews", ["maintenance_request_id"])

    op.create_table(
        "arsenal_engineering_instructions",
        *audit_columns(),
        sa.Column("engineering_review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instruction_code", sa.String(length=120), nullable=False),
        sa.Column("procedure_description", sa.Text(), nullable=False),
        sa.Column("required_tools", sa.Text(), nullable=True),
        sa.Column("required_parts", sa.Text(), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=True),
        sa.Column("issued_by", sa.String(length=180), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["engineering_review_id"], ["arsenal_engineering_reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instruction_code"),
    )
    op.create_index("ix_arsenal_engineering_instructions_engineering_review_id", "arsenal_engineering_instructions", ["engineering_review_id"])
    op.create_index("ix_arsenal_engineering_instructions_is_deleted", "arsenal_engineering_instructions", ["is_deleted"])

    op.create_table(
        "arsenal_repair_tasks",
        *audit_columns(),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_technician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engineering_instruction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repair_notes", sa.Text(), nullable=True),
        sa.Column("status", repair_status, nullable=False),
        sa.ForeignKeyConstraint(["engineering_instruction_id"], ["arsenal_engineering_instructions.id"]),
        sa.ForeignKeyConstraint(["maintenance_request_id"], ["arsenal_maintenance_requests.id"]),
        sa.ForeignKeyConstraint(["section_assignment_id"], ["arsenal_section_assignments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_repair_tasks_assigned_technician_id", "arsenal_repair_tasks", ["assigned_technician_id"])
    op.create_index("ix_arsenal_repair_tasks_engineering_instruction_id", "arsenal_repair_tasks", ["engineering_instruction_id"])
    op.create_index("ix_arsenal_repair_tasks_is_deleted", "arsenal_repair_tasks", ["is_deleted"])
    op.create_index("ix_arsenal_repair_tasks_maintenance_request_id", "arsenal_repair_tasks", ["maintenance_request_id"])
    op.create_index("ix_arsenal_repair_tasks_section_assignment_id", "arsenal_repair_tasks", ["section_assignment_id"])

    op.create_table(
        "arsenal_quality_inspections",
        *audit_columns(),
        sa.Column("repair_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspector_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspection_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("inspection_notes", sa.Text(), nullable=True),
        sa.Column("certification_number", sa.String(length=120), nullable=True),
        sa.Column("status", inspection_status, nullable=False),
        sa.ForeignKeyConstraint(["repair_task_id"], ["arsenal_repair_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_quality_inspections_inspector_id", "arsenal_quality_inspections", ["inspector_id"])
    op.create_index("ix_arsenal_quality_inspections_is_deleted", "arsenal_quality_inspections", ["is_deleted"])
    op.create_index("ix_arsenal_quality_inspections_repair_task_id", "arsenal_quality_inspections", ["repair_task_id"])

    op.create_table(
        "arsenal_service_releases",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_inspection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("released_by", sa.String(length=180), nullable=False),
        sa.Column("release_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_condition", sa.String(length=120), nullable=False),
        sa.Column("returned_to_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", release_status, nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["quality_inspection_id"], ["arsenal_quality_inspections.id"]),
        sa.ForeignKeyConstraint(["returned_to_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arsenal_service_releases_asset_id", "arsenal_service_releases", ["asset_id"])
    op.create_index("ix_arsenal_service_releases_is_deleted", "arsenal_service_releases", ["is_deleted"])
    op.create_index("ix_arsenal_service_releases_quality_inspection_id", "arsenal_service_releases", ["quality_inspection_id"])
    op.create_index("ix_arsenal_service_releases_returned_to_department_id", "arsenal_service_releases", ["returned_to_department_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.String(length=180), nullable=False),
        sa.Column("action", sa.String(length=240), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_arsenal_service_releases_returned_to_department_id", table_name="arsenal_service_releases")
    op.drop_index("ix_arsenal_service_releases_quality_inspection_id", table_name="arsenal_service_releases")
    op.drop_index("ix_arsenal_service_releases_is_deleted", table_name="arsenal_service_releases")
    op.drop_index("ix_arsenal_service_releases_asset_id", table_name="arsenal_service_releases")
    op.drop_table("arsenal_service_releases")
    op.drop_index("ix_arsenal_quality_inspections_repair_task_id", table_name="arsenal_quality_inspections")
    op.drop_index("ix_arsenal_quality_inspections_is_deleted", table_name="arsenal_quality_inspections")
    op.drop_index("ix_arsenal_quality_inspections_inspector_id", table_name="arsenal_quality_inspections")
    op.drop_table("arsenal_quality_inspections")
    op.drop_index("ix_arsenal_repair_tasks_section_assignment_id", table_name="arsenal_repair_tasks")
    op.drop_index("ix_arsenal_repair_tasks_maintenance_request_id", table_name="arsenal_repair_tasks")
    op.drop_index("ix_arsenal_repair_tasks_is_deleted", table_name="arsenal_repair_tasks")
    op.drop_index("ix_arsenal_repair_tasks_engineering_instruction_id", table_name="arsenal_repair_tasks")
    op.drop_index("ix_arsenal_repair_tasks_assigned_technician_id", table_name="arsenal_repair_tasks")
    op.drop_table("arsenal_repair_tasks")
    op.drop_index("ix_arsenal_engineering_instructions_is_deleted", table_name="arsenal_engineering_instructions")
    op.drop_index("ix_arsenal_engineering_instructions_engineering_review_id", table_name="arsenal_engineering_instructions")
    op.drop_table("arsenal_engineering_instructions")
    op.drop_index("ix_arsenal_engineering_reviews_maintenance_request_id", table_name="arsenal_engineering_reviews")
    op.drop_index("ix_arsenal_engineering_reviews_is_deleted", table_name="arsenal_engineering_reviews")
    op.drop_index("ix_arsenal_engineering_reviews_engineer_id", table_name="arsenal_engineering_reviews")
    op.drop_table("arsenal_engineering_reviews")
    op.drop_index("ix_arsenal_section_assignments_maintenance_request_id", table_name="arsenal_section_assignments")
    op.drop_index("ix_arsenal_section_assignments_is_deleted", table_name="arsenal_section_assignments")
    op.drop_index("ix_arsenal_section_assignments_assigned_section_id", table_name="arsenal_section_assignments")
    op.drop_table("arsenal_section_assignments")
    op.drop_index("ix_arsenal_component_receptions_received_by_department_id", table_name="arsenal_component_receptions")
    op.drop_index("ix_arsenal_component_receptions_maintenance_request_id", table_name="arsenal_component_receptions")
    op.drop_index("ix_arsenal_component_receptions_is_deleted", table_name="arsenal_component_receptions")
    op.drop_table("arsenal_component_receptions")
    op.drop_index("ix_arsenal_maintenance_requests_origin_department_id", table_name="arsenal_maintenance_requests")
    op.drop_index("ix_arsenal_maintenance_requests_is_deleted", table_name="arsenal_maintenance_requests")
    op.drop_index("ix_arsenal_maintenance_requests_failure_report_id", table_name="arsenal_maintenance_requests")
    op.drop_index("ix_arsenal_maintenance_requests_asset_id", table_name="arsenal_maintenance_requests")
    op.drop_table("arsenal_maintenance_requests")

    bind = op.get_bind()
    for enum_name in (
        "arsenal_service_release_status",
        "arsenal_quality_inspection_status",
        "arsenal_repair_task_status",
        "arsenal_engineering_review_status",
        "arsenal_section_assignment_status",
        "arsenal_component_reception_status",
        "arsenal_section_assignment_priority",
        "arsenal_maintenance_request_priority",
        "arsenal_maintenance_request_status",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
