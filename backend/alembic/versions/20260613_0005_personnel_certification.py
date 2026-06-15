"""personnel certification module

Revision ID: 20260613_0005
Revises: 20260613_0004
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0005"
down_revision: str | None = "20260613_0004"
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
    certification_level = postgresql.ENUM("LEVEL_A", "LEVEL_B", "LEVEL_C", "INSPECTOR", name="personnel_certification_level", create_type=False)
    technician_certification_level = postgresql.ENUM("LEVEL_A", "LEVEL_B", "LEVEL_C", "INSPECTOR", name="personnel_technician_certification_level", create_type=False)
    minimum_level = postgresql.ENUM("LEVEL_A", "LEVEL_B", "LEVEL_C", name="personnel_certification_minimum_level", create_type=False)
    audit_event_type = postgresql.ENUM("CREATED", "UPGRADED", "REVOKED", "EXPIRED", "RENEWED", name="personnel_certification_audit_event_type", create_type=False)
    audit_previous_level = postgresql.ENUM("LEVEL_A", "LEVEL_B", "LEVEL_C", "INSPECTOR", name="personnel_certification_audit_previous_level", create_type=False)
    audit_new_level = postgresql.ENUM("LEVEL_A", "LEVEL_B", "LEVEL_C", "INSPECTOR", name="personnel_certification_audit_new_level", create_type=False)

    bind = op.get_bind()
    for enum in (
        certification_level,
        technician_certification_level,
        minimum_level,
        audit_event_type,
        audit_previous_level,
        audit_new_level,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "personnel_technician_profiles",
        *audit_columns(),
        sa.Column("personnel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technical_code", sa.String(length=80), nullable=False),
        sa.Column("join_date", sa.Date(), nullable=False),
        sa.Column("current_level", certification_level, nullable=False),
        sa.Column("years_of_experience", sa.Numeric(5, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("personnel_id"),
        sa.UniqueConstraint("technical_code"),
    )
    op.create_index("ix_personnel_technician_profiles_is_deleted", "personnel_technician_profiles", ["is_deleted"])
    op.create_index("ix_personnel_technician_profiles_personnel_id", "personnel_technician_profiles", ["personnel_id"])

    op.create_table(
        "personnel_technical_specializations",
        *audit_columns(),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_personnel_technical_specializations_is_deleted", "personnel_technical_specializations", ["is_deleted"])

    op.create_table(
        "personnel_technician_certifications",
        *audit_columns(),
        sa.Column("technician_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specialization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("certification_level", technician_certification_level, nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("issued_by", sa.String(length=180), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["specialization_id"], ["personnel_technical_specializations.id"]),
        sa.ForeignKeyConstraint(["technician_profile_id"], ["personnel_technician_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_technician_certifications_is_deleted", "personnel_technician_certifications", ["is_deleted"])
    op.create_index("ix_personnel_technician_certifications_specialization_id", "personnel_technician_certifications", ["specialization_id"])
    op.create_index("ix_personnel_technician_certifications_technician_profile_id", "personnel_technician_certifications", ["technician_profile_id"])

    op.create_table(
        "personnel_certification_requirements",
        *audit_columns(),
        sa.Column("task_type", sa.String(length=160), nullable=False),
        sa.Column("required_specialization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("minimum_level", minimum_level, nullable=False),
        sa.Column("requires_inspector_approval", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["required_specialization_id"], ["personnel_technical_specializations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_type", "required_specialization_id", name="uq_certification_requirement_task_specialization"),
    )
    op.create_index("ix_personnel_certification_requirements_is_deleted", "personnel_certification_requirements", ["is_deleted"])
    op.create_index("ix_personnel_cert_req_specialization_id", "personnel_certification_requirements", ["required_specialization_id"])
    op.create_index("ix_personnel_certification_requirements_task_type", "personnel_certification_requirements", ["task_type"])

    op.create_table(
        "personnel_technician_experience_records",
        *audit_columns(),
        sa.Column("technician_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(length=160), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hours_worked", sa.Numeric(8, 2), nullable=False),
        sa.Column("supervised_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["technician_profile_id"], ["personnel_technician_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_technician_experience_records_asset_id", "personnel_technician_experience_records", ["asset_id"])
    op.create_index("ix_personnel_technician_experience_records_is_deleted", "personnel_technician_experience_records", ["is_deleted"])
    op.create_index("ix_personnel_technician_experience_records_supervised_by", "personnel_technician_experience_records", ["supervised_by"])
    op.create_index("ix_personnel_technician_experience_records_task_type", "personnel_technician_experience_records", ["task_type"])
    op.create_index("ix_personnel_exp_records_profile_id", "personnel_technician_experience_records", ["technician_profile_id"])

    op.create_table(
        "personnel_task_authorizations",
        *audit_columns(),
        sa.Column("technician_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(length=160), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("authorized", sa.Boolean(), nullable=False),
        sa.Column("authorization_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("authorized_by", sa.String(length=180), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["technician_profile_id"], ["personnel_technician_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_task_authorizations_asset_id", "personnel_task_authorizations", ["asset_id"])
    op.create_index("ix_personnel_task_authorizations_is_deleted", "personnel_task_authorizations", ["is_deleted"])
    op.create_index("ix_personnel_task_authorizations_task_type", "personnel_task_authorizations", ["task_type"])
    op.create_index("ix_personnel_task_authorizations_technician_profile_id", "personnel_task_authorizations", ["technician_profile_id"])

    op.create_table(
        "personnel_certification_audits",
        *audit_columns(),
        sa.Column("technician_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("previous_level", audit_previous_level, nullable=True),
        sa.Column("new_level", audit_new_level, nullable=True),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["technician_profile_id"], ["personnel_technician_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_certification_audits_is_deleted", "personnel_certification_audits", ["is_deleted"])
    op.create_index("ix_personnel_certification_audits_technician_profile_id", "personnel_certification_audits", ["technician_profile_id"])


def downgrade() -> None:
    op.drop_index("ix_personnel_certification_audits_technician_profile_id", table_name="personnel_certification_audits")
    op.drop_index("ix_personnel_certification_audits_is_deleted", table_name="personnel_certification_audits")
    op.drop_table("personnel_certification_audits")
    op.drop_index("ix_personnel_task_authorizations_technician_profile_id", table_name="personnel_task_authorizations")
    op.drop_index("ix_personnel_task_authorizations_task_type", table_name="personnel_task_authorizations")
    op.drop_index("ix_personnel_task_authorizations_is_deleted", table_name="personnel_task_authorizations")
    op.drop_index("ix_personnel_task_authorizations_asset_id", table_name="personnel_task_authorizations")
    op.drop_table("personnel_task_authorizations")
    op.drop_index("ix_personnel_exp_records_profile_id", table_name="personnel_technician_experience_records")
    op.drop_index("ix_personnel_technician_experience_records_task_type", table_name="personnel_technician_experience_records")
    op.drop_index("ix_personnel_technician_experience_records_supervised_by", table_name="personnel_technician_experience_records")
    op.drop_index("ix_personnel_technician_experience_records_is_deleted", table_name="personnel_technician_experience_records")
    op.drop_index("ix_personnel_technician_experience_records_asset_id", table_name="personnel_technician_experience_records")
    op.drop_table("personnel_technician_experience_records")
    op.drop_index("ix_personnel_certification_requirements_task_type", table_name="personnel_certification_requirements")
    op.drop_index("ix_personnel_cert_req_specialization_id", table_name="personnel_certification_requirements")
    op.drop_index("ix_personnel_certification_requirements_is_deleted", table_name="personnel_certification_requirements")
    op.drop_table("personnel_certification_requirements")
    op.drop_index("ix_personnel_technician_certifications_technician_profile_id", table_name="personnel_technician_certifications")
    op.drop_index("ix_personnel_technician_certifications_specialization_id", table_name="personnel_technician_certifications")
    op.drop_index("ix_personnel_technician_certifications_is_deleted", table_name="personnel_technician_certifications")
    op.drop_table("personnel_technician_certifications")
    op.drop_index("ix_personnel_technical_specializations_is_deleted", table_name="personnel_technical_specializations")
    op.drop_table("personnel_technical_specializations")
    op.drop_index("ix_personnel_technician_profiles_personnel_id", table_name="personnel_technician_profiles")
    op.drop_index("ix_personnel_technician_profiles_is_deleted", table_name="personnel_technician_profiles")
    op.drop_table("personnel_technician_profiles")

    bind = op.get_bind()
    for enum_name in (
        "personnel_certification_audit_new_level",
        "personnel_certification_audit_previous_level",
        "personnel_certification_audit_event_type",
        "personnel_certification_minimum_level",
        "personnel_technician_certification_level",
        "personnel_certification_level",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
