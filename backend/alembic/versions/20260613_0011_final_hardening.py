"""Create final operational hardening tables (AOG, Deferred Defects, Slots, Calibration, Physical Documents, External Repairs, Classification)

Revision ID: 20260613_0011
Revises: 20260613_0010
Create Date: 2026-06-13 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260613_0011'
down_revision: Union[str, None] = '20260613_0010_advanced'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modificar tabla assets (Vida Límite LLP)
    op.create_table(
        'assets_life_limited_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('life_limit_hours', sa.Float(), nullable=False),
        sa.Column('life_limit_cycles', sa.Integer(), nullable=False),
        sa.Column('consumed_hours', sa.Float(), nullable=False),
        sa.Column('consumed_cycles', sa.Integer(), nullable=False),
        sa.Column('remaining_hours', sa.Float(), nullable=False),
        sa.Column('remaining_cycles', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_life_limited_components_asset_id'), 'assets_life_limited_components', ['asset_id'], unique=True)

    # 2. Modificar tabla engine_trend_monitoring y engine_oil_analysis_records (Metales y Telemetría)
    op.add_column('engine_trend_monitoring', sa.Column('egt_c', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_trend_monitoring', sa.Column('torque_percent', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_trend_monitoring', sa.Column('n1_percent', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_trend_monitoring', sa.Column('n2_percent', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_trend_monitoring', sa.Column('fuel_flow_gph', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_trend_monitoring', sa.Column('oil_temperature_c', sa.Float(), nullable=False, server_default='0.0'))

    op.add_column('engine_oil_analysis_records', sa.Column('aluminum_ppm', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_oil_analysis_records', sa.Column('chrome_ppm', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_oil_analysis_records', sa.Column('nickel_ppm', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('engine_oil_analysis_records', sa.Column('contamination_detected', sa.Boolean(), nullable=False, server_default='0'))

    # 3. Tabla: engine_installation_history
    op.create_table(
        'engine_installation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('aircraft_hours_at_installation', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('aircraft_hours_at_removal', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('engine_hours_accumulated', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['engine_asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_installation_history_engine_asset_id'), 'engine_installation_history', ['engine_asset_id'], unique=False)
    op.create_index(op.f('ix_engine_installation_history_aircraft_asset_id'), 'engine_installation_history', ['aircraft_asset_id'], unique=False)

    # 4. Tabla: flight_release_authorizations
    op.create_table(
        'flight_release_authorizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('authorized_by', sa.String(length=180), nullable=False),
        sa.Column('authorization_type', sa.String(length=80), nullable=False),
        sa.Column('authorized_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flight_release_authorizations_aircraft_id'), 'flight_release_authorizations', ['aircraft_id'], unique=False)

    # 5. Tablas: maintenance_task_executions y maintenance_dual_inspections
    op.create_table(
        'maintenance_task_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certification_level', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('digital_signature_hash', sa.String(length=240), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maintenance_task_executions_task_id'), 'maintenance_task_executions', ['task_id'], unique=False)
    op.create_index(op.f('ix_maintenance_task_executions_asset_id'), 'maintenance_task_executions', ['asset_id'], unique=False)
    op.create_index(op.f('ix_maintenance_task_executions_technician_id'), 'maintenance_task_executions', ['technician_id'], unique=False)

    op.create_table(
        'maintenance_dual_inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspector_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('second_inspector_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['maintenance_task_executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maintenance_dual_inspections_execution_id'), 'maintenance_dual_inspections', ['execution_id'], unique=False)

    # 6. Tabla: airworthiness_decisions
    op.create_table(
        'airworthiness_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_status', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('decided_by', sa.String(length=180), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_airworthiness_decisions_aircraft_id'), 'airworthiness_decisions', ['aircraft_id'], unique=False)

    # 7. Tablas: disposal_requests y disposal_approvals
    op.create_table(
        'disposal_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.String(length=120), nullable=False),
        sa.Column('initiated_by', sa.String(length=180), nullable=False),
        sa.Column('engineering_review_required', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disposal_requests_asset_id'), 'disposal_requests', ['asset_id'], unique=False)

    op.create_table(
        'disposal_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('disposal_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', sa.String(length=180), nullable=False),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['disposal_request_id'], ['disposal_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disposal_approvals_disposal_request_id'), 'disposal_approvals', ['disposal_request_id'], unique=False)

    # 8. Tabla: asset_reallocations
    op.create_table(
        'asset_reallocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('donor_aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receiver_aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('component_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority_reason', sa.String(length=120), nullable=False),
        sa.Column('authorized_by', sa.String(length=180), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['donor_aircraft_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['receiver_aircraft_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['component_asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_reallocations_donor_aircraft_id'), 'asset_reallocations', ['donor_aircraft_id'], unique=False)
    op.create_index(op.f('ix_asset_reallocations_receiver_aircraft_id'), 'asset_reallocations', ['receiver_aircraft_id'], unique=False)
    op.create_index(op.f('ix_asset_reallocations_component_asset_id'), 'asset_reallocations', ['component_asset_id'], unique=False)

    # 9. Tablas: configuration_baselines y configuration_deviations
    op.create_table(
        'configuration_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_configuration_json', sa.JSON(), nullable=False),
        sa.Column('approved_by_engineering', sa.String(length=180), nullable=False),
        sa.Column('revision_number', sa.String(length=50), nullable=False),
        sa.Column('certification_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuration_baselines_aircraft_model_id'), 'configuration_baselines', ['aircraft_model_id'], unique=False)

    op.create_table(
        'configuration_deviations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deviation_type', sa.String(length=80), nullable=False),
        sa.Column('approved_by', sa.String(length=180), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuration_deviations_aircraft_id'), 'configuration_deviations', ['aircraft_id'], unique=False)

    # 10. Tabla: structural_fatigue_records
    op.create_table(
        'structural_fatigue_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accumulated_cycles', sa.Integer(), nullable=False),
        sa.Column('g_force_cycles', sa.Integer(), nullable=False),
        sa.Column('landing_cycles', sa.Integer(), nullable=False),
        sa.Column('corrosion_index', sa.Float(), nullable=False),
        sa.Column('crack_detection_level', sa.Float(), nullable=False),
        sa.Column('inspection_interval_remaining', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id')
    )
    op.create_index(op.f('ix_structural_fatigue_records_asset_id'), 'structural_fatigue_records', ['asset_id'], unique=True)

    # 11. Tabla: maintenance_human_factor_incidents
    op.create_table(
        'maintenance_human_factor_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_type', sa.String(length=100), nullable=False),
        sa.Column('severity_level', sa.String(length=50), nullable=False),
        sa.Column('investigation_required', sa.Boolean(), nullable=False),
        sa.Column('corrective_action_required', sa.Boolean(), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['maintenance_task_executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maintenance_human_factor_incidents_technician_id'), 'maintenance_human_factor_incidents', ['technician_id'], unique=False)
    op.create_index(op.f('ix_maintenance_human_factor_incidents_task_id'), 'maintenance_human_factor_incidents', ['task_id'], unique=False)
    op.create_index(op.f('ix_maintenance_human_factor_incidents_asset_id'), 'maintenance_human_factor_incidents', ['asset_id'], unique=False)

    # 12. Tabla: reliability_trends
    op.create_table(
        'reliability_trends',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mtbf', sa.Float(), nullable=False),
        sa.Column('mttr', sa.Float(), nullable=False),
        sa.Column('repeated_failures_count', sa.Integer(), nullable=False),
        sa.Column('failure_rate_per_100_hours', sa.Float(), nullable=False),
        sa.Column('reliability_score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id')
    )
    op.create_index(op.f('ix_reliability_trends_asset_id'), 'reliability_trends', ['asset_id'], unique=True)

    # 13. Modificar tabla tools_usage_records (Checkout y Checkin de Herramientas)
    op.create_table(
        'tools_usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checked_out_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calibration_valid_at_usage', sa.Boolean(), nullable=False),
        sa.Column('damage_detected', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tools_usage_records_tool_id'), 'tools_usage_records', ['tool_id'], unique=False)
    op.create_index(op.f('ix_tools_usage_records_technician_id'), 'tools_usage_records', ['technician_id'], unique=False)
    op.create_index(op.f('ix_tools_usage_records_task_id'), 'tools_usage_records', ['task_id'], unique=False)

    # 14. Tablas: fod_inspections y fod_incidents
    op.create_table(
        'fod_inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspection_location', sa.String(length=120), nullable=False),
        sa.Column('performed_by', sa.String(length=180), nullable=False),
        sa.Column('findings', sa.Text(), nullable=True),
        sa.Column('cleared_for_operation', sa.Boolean(), nullable=False),
        sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fod_inspections_aircraft_id'), 'fod_inspections', ['aircraft_id'], unique=False)

    op.create_table(
        'fod_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('foreign_object_type', sa.String(length=120), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fod_incidents_asset_id'), 'fod_incidents', ['asset_id'], unique=False)


def downgrade() -> None:
    op.drop_table('fod_incidents')
    op.drop_table('fod_inspections')
    op.drop_table('tools_usage_records')
    op.drop_table('reliability_trends')
    op.drop_table('maintenance_human_factor_incidents')
    op.drop_table('structural_fatigue_records')
    op.drop_table('configuration_deviations')
    op.drop_table('configuration_baselines')
    op.drop_table('asset_reallocations')
    op.drop_table('disposal_approvals')
    op.drop_table('disposal_requests')
    op.drop_table('airworthiness_decisions')
    op.drop_table('maintenance_dual_inspections')
    op.drop_table('maintenance_task_executions')
    op.drop_table('flight_release_authorizations')
    op.drop_table('engine_installation_history')
    
    op.drop_column('engine_oil_analysis_records', 'contamination_detected')
    op.drop_column('engine_oil_analysis_records', 'nickel_ppm')
    op.drop_column('engine_oil_analysis_records', 'chrome_ppm')
    op.drop_column('engine_oil_analysis_records', 'aluminum_ppm')
    
    op.drop_column('engine_trend_monitoring', 'oil_temperature_c')
    op.drop_column('engine_trend_monitoring', 'fuel_flow_gph')
    op.drop_column('engine_trend_monitoring', 'n2_percent')
    op.drop_column('engine_trend_monitoring', 'n1_percent')
    op.drop_column('engine_trend_monitoring', 'torque_percent')
    op.drop_column('engine_trend_monitoring', 'egt_c')
    
    op.drop_table('assets_life_limited_components')
