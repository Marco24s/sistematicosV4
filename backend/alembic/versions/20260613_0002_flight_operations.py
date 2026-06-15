"""flight operations module

Revision ID: 20260613_0002
Revises: 20260613_0001
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0002"
down_revision: str | None = "20260613_0001"
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
    mission_status = postgresql.ENUM("PLANNED", "APPROVED", "IN_PROGRESS", "COMPLETED", "CANCELED", name="mission_status", create_type=False)
    mission_type = postgresql.ENUM("TRAINING", "TRANSPORT", "SEARCH_AND_RESCUE", "PATROL", "TEST_FLIGHT", name="mission_type", create_type=False)
    crew_role = postgresql.ENUM("PILOT", "COPILOT", "FLIGHT_ENGINEER", "CREW_CHIEF", "OBSERVER", name="crew_role", create_type=False)
    flight_sheet_status = postgresql.ENUM("PREPARED", "AIRBORNE", "LANDED", "CLOSED", name="flight_sheet_status", create_type=False)
    installed_asset_status = postgresql.ENUM("INSTALLED", "REMOVED", name="installed_asset_status", create_type=False)
    installation_event_type = postgresql.ENUM("INSTALL", "REMOVE", name="installation_event_type", create_type=False)
    consumption_type = postgresql.ENUM("FLIGHT_HOURS", "CYCLES", name="consumption_type", create_type=False)
    operational_alert_severity = postgresql.ENUM("INFO", "WARNING", "CRITICAL", name="operational_alert_severity", create_type=False)
    operational_alert_status = postgresql.ENUM("OPEN", "ACKNOWLEDGED", "CLOSED", name="operational_alert_status", create_type=False)

    bind = op.get_bind()
    for enum in (
        mission_status,
        mission_type,
        crew_role,
        flight_sheet_status,
        installed_asset_status,
        installation_event_type,
        consumption_type,
        operational_alert_severity,
        operational_alert_status,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "missions",
        *audit_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mission_code", sa.String(length=80), nullable=False),
        sa.Column("mission_type", mission_type, nullable=False),
        sa.Column("planned_flight_hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", mission_status, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "mission_code", name="uq_missions_organization_code"),
    )
    op.create_index("ix_missions_is_deleted", "missions", ["is_deleted"])
    op.create_index("ix_missions_organization_id", "missions", ["organization_id"])

    op.create_table(
        "crew_assignments",
        *audit_columns(),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("personnel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", crew_role, nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mission_id", "personnel_id", "role", name="uq_crew_assignment_role"),
    )
    op.create_index("ix_crew_assignments_is_deleted", "crew_assignments", ["is_deleted"])
    op.create_index("ix_crew_assignments_mission_id", "crew_assignments", ["mission_id"])
    op.create_index("ix_crew_assignments_personnel_id", "crew_assignments", ["personnel_id"])

    op.create_table(
        "flight_sheets",
        *audit_columns(),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fuel_loaded", sa.Numeric(10, 2), nullable=False),
        sa.Column("aircraft_weight", sa.Numeric(10, 2), nullable=False),
        sa.Column("planned_departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("actual_hours_flown", sa.Numeric(8, 2), nullable=True),
        sa.Column("technical_observations", sa.Text(), nullable=True),
        sa.Column("reported_failures", sa.Text(), nullable=True),
        sa.Column("status", flight_sheet_status, nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mission_id"),
    )
    op.create_index("ix_flight_sheets_aircraft_asset_id", "flight_sheets", ["aircraft_asset_id"])
    op.create_index("ix_flight_sheets_is_deleted", "flight_sheets", ["is_deleted"])
    op.create_index("ix_flight_sheets_mission_id", "flight_sheets", ["mission_id"])

    op.create_table(
        "installed_assets",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("installed_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_code", sa.String(length=80), nullable=False),
        sa.Column("installation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("installed_by", sa.String(length=180), nullable=False),
        sa.Column("status", installed_asset_status, nullable=False),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["installed_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aircraft_asset_id", "installed_asset_id", "status", name="uq_installed_asset_status"),
    )
    op.create_index("ix_installed_assets_aircraft_asset_id", "installed_assets", ["aircraft_asset_id"])
    op.create_index("ix_installed_assets_installed_asset_id", "installed_assets", ["installed_asset_id"])
    op.create_index("ix_installed_assets_is_deleted", "installed_assets", ["is_deleted"])

    op.create_table(
        "installation_events",
        *audit_columns(),
        sa.Column("aircraft_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", installation_event_type, nullable=False),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["aircraft_asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installation_events_aircraft_asset_id", "installation_events", ["aircraft_asset_id"])
    op.create_index("ix_installation_events_asset_id", "installation_events", ["asset_id"])
    op.create_index("ix_installation_events_is_deleted", "installation_events", ["is_deleted"])

    op.create_table(
        "flight_hour_consumption_events",
        *audit_columns(),
        sa.Column("flight_sheet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consumption_type", consumption_type, nullable=False),
        sa.Column("hours_consumed", sa.Numeric(8, 2), nullable=False),
        sa.Column("cycles_consumed", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["flight_sheet_id"], ["flight_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flight_hour_consumption_events_asset_id", "flight_hour_consumption_events", ["asset_id"])
    op.create_index("ix_flight_hour_consumption_events_flight_sheet_id", "flight_hour_consumption_events", ["flight_sheet_id"])
    op.create_index("ix_flight_hour_consumption_events_is_deleted", "flight_hour_consumption_events", ["is_deleted"])

    op.create_table(
        "operational_alerts",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flight_sheet_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", operational_alert_severity, nullable=False),
        sa.Column("status", operational_alert_status, nullable=False),
        sa.Column("alert_code", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["flight_sheet_id"], ["flight_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operational_alerts_asset_id", "operational_alerts", ["asset_id"])
    op.create_index("ix_operational_alerts_flight_sheet_id", "operational_alerts", ["flight_sheet_id"])
    op.create_index("ix_operational_alerts_is_deleted", "operational_alerts", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_operational_alerts_is_deleted", table_name="operational_alerts")
    op.drop_index("ix_operational_alerts_flight_sheet_id", table_name="operational_alerts")
    op.drop_index("ix_operational_alerts_asset_id", table_name="operational_alerts")
    op.drop_table("operational_alerts")
    op.drop_index("ix_flight_hour_consumption_events_is_deleted", table_name="flight_hour_consumption_events")
    op.drop_index("ix_flight_hour_consumption_events_flight_sheet_id", table_name="flight_hour_consumption_events")
    op.drop_index("ix_flight_hour_consumption_events_asset_id", table_name="flight_hour_consumption_events")
    op.drop_table("flight_hour_consumption_events")
    op.drop_index("ix_installation_events_is_deleted", table_name="installation_events")
    op.drop_index("ix_installation_events_asset_id", table_name="installation_events")
    op.drop_index("ix_installation_events_aircraft_asset_id", table_name="installation_events")
    op.drop_table("installation_events")
    op.drop_index("ix_installed_assets_is_deleted", table_name="installed_assets")
    op.drop_index("ix_installed_assets_installed_asset_id", table_name="installed_assets")
    op.drop_index("ix_installed_assets_aircraft_asset_id", table_name="installed_assets")
    op.drop_table("installed_assets")
    op.drop_index("ix_flight_sheets_mission_id", table_name="flight_sheets")
    op.drop_index("ix_flight_sheets_is_deleted", table_name="flight_sheets")
    op.drop_index("ix_flight_sheets_aircraft_asset_id", table_name="flight_sheets")
    op.drop_table("flight_sheets")
    op.drop_index("ix_crew_assignments_personnel_id", table_name="crew_assignments")
    op.drop_index("ix_crew_assignments_mission_id", table_name="crew_assignments")
    op.drop_index("ix_crew_assignments_is_deleted", table_name="crew_assignments")
    op.drop_table("crew_assignments")
    op.drop_index("ix_missions_organization_id", table_name="missions")
    op.drop_index("ix_missions_is_deleted", table_name="missions")
    op.drop_table("missions")

    bind = op.get_bind()
    for enum_name in (
        "operational_alert_status",
        "operational_alert_severity",
        "consumption_type",
        "installation_event_type",
        "installed_asset_status",
        "flight_sheet_status",
        "crew_role",
        "mission_type",
        "mission_status",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
