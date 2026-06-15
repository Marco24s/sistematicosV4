"""Add engine management, reporting analytics, serialized inventory, config snapshots, and unit isolation

Revision ID: 20260613_0010
Revises: 20260613_0009
Create Date: 2026-06-13 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260613_0010_advanced'
down_revision: Union[str, None] = '20260613_0010_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modificar tabla supply_chain_stock_items
    op.add_column('supply_chain_stock_items', sa.Column('serial_number', sa.String(length=120), nullable=True))
    op.add_column('supply_chain_stock_items', sa.Column('batch_number', sa.String(length=120), nullable=True))
    op.add_column('supply_chain_stock_items', sa.Column('lot_number', sa.String(length=120), nullable=True))
    op.add_column('supply_chain_stock_items', sa.Column('serialized_inventory', sa.Boolean(), nullable=False, server_default='0'))
    
    op.add_column('supply_chain_stock_items', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('supply_chain_stock_items', sa.Column('military_unit_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('supply_chain_stock_items', sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_supply_chain_stock_items_organization_id'), 'supply_chain_stock_items', ['organization_id'], unique=False)
    op.create_index(op.f('ix_supply_chain_stock_items_military_unit_id'), 'supply_chain_stock_items', ['military_unit_id'], unique=False)
    op.create_index(op.f('ix_supply_chain_stock_items_department_id'), 'supply_chain_stock_items', ['department_id'], unique=False)

    # 2. Tabla: supply_chain_stock_movement_history
    op.create_table(
        'supply_chain_stock_movement_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stock_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('moved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('moved_by', sa.String(length=180), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['from_location_id'], ['supply_chain_inventory_locations.id'], ),
        sa.ForeignKeyConstraint(['to_location_id'], ['supply_chain_inventory_locations.id'], ),
        sa.ForeignKeyConstraint(['stock_item_id'], ['supply_chain_stock_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_supply_chain_stock_movement_history_stock_item_id'), 'supply_chain_stock_movement_history', ['stock_item_id'], unique=False)

    # 3. Tablas de engine_management
    op.create_table(
        'engine_assemblies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_model', sa.String(length=120), nullable=False),
        sa.Column('serial_number', sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number')
    )
    op.create_index(op.f('ix_engine_assemblies_asset_id'), 'engine_assemblies', ['asset_id'], unique=True)

    op.create_table(
        'engine_submodules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submodule_name', sa.String(length=120), nullable=False),
        sa.Column('serial_number', sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number')
    )
    op.create_index(op.f('ix_engine_submodules_engine_assembly_id'), 'engine_submodules', ['engine_assembly_id'], unique=False)

    op.create_table(
        'engine_inspection_programs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspection_name', sa.String(length=180), nullable=False),
        sa.Column('interval_hours', sa.Integer(), nullable=False),
        sa.Column('last_performed_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('next_due_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_inspection_programs_engine_assembly_id'), 'engine_inspection_programs', ['engine_assembly_id'], unique=False)

    op.create_table(
        'engine_cycle_counters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_operating_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_start_cycles', sa.Integer(), nullable=False),
        sa.Column('total_ng_cycles', sa.Integer(), nullable=False),
        sa.Column('total_np_cycles', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_cycle_counters_engine_assembly_id'), 'engine_cycle_counters', ['engine_assembly_id'], unique=True)

    op.create_table(
        'engine_trend_monitoring',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('turbine_temperature_c', sa.Float(), nullable=False),
        sa.Column('oil_pressure_psi', sa.Float(), nullable=False),
        sa.Column('vibration_level', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_trend_monitoring_engine_assembly_id'), 'engine_trend_monitoring', ['engine_assembly_id'], unique=False)

    op.create_table(
        'engine_oil_analysis_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sampled_at', sa.Date(), nullable=False),
        sa.Column('iron_ppm', sa.Float(), nullable=False),
        sa.Column('copper_ppm', sa.Float(), nullable=False),
        sa.Column('silicon_ppm', sa.Float(), nullable=False),
        sa.Column('verdict', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_oil_analysis_records_engine_assembly_id'), 'engine_oil_analysis_records', ['engine_assembly_id'], unique=False)

    op.create_table(
        'engine_hot_section_inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_assembly_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspected_at_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('inspected_date', sa.Date(), nullable=False),
        sa.Column('performed_by', sa.String(length=180), nullable=False),
        sa.Column('findings', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['engine_assembly_id'], ['engine_assemblies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engine_hot_section_inspections_engine_assembly_id'), 'engine_hot_section_inspections', ['engine_assembly_id'], unique=False)

    # 4. Tabla: squadron_aircraft_configuration_snapshots
    op.create_table(
        'squadron_aircraft_configuration_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('flight_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('installed_components_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(length=180), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_squadron_aircraft_configuration_snapshots_aircraft_id'), 'squadron_aircraft_configuration_snapshots', ['aircraft_id'], unique=False)

    # 5. Tablas de reporting_analytics
    op.create_table(
        'reporting_fleet_availability',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('total_aircraft', sa.Integer(), nullable=False),
        sa.Column('available_aircraft', sa.Integer(), nullable=False),
        sa.Column('non_operational_aircraft', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_date')
    )
    op.create_index(op.f('ix_reporting_fleet_availability_report_date'), 'reporting_fleet_availability', ['report_date'], unique=True)

    op.create_table(
        'reporting_mtbf',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mean_time_between_failures_hours', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_mtbf_asset_type_id'), 'reporting_mtbf', ['asset_type_id'], unique=False)

    op.create_table(
        'reporting_mttr',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mean_time_to_repair_days', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_mttr_asset_type_id'), 'reporting_mttr', ['asset_type_id'], unique=False)

    op.create_table(
        'reporting_section_repair_times',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('average_repair_days', sa.Float(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_section_repair_times_section_id'), 'reporting_section_repair_times', ['section_id'], unique=False)

    op.create_table(
        'reporting_technician_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tasks_completed', sa.Integer(), nullable=False),
        sa.Column('average_rating', sa.Float(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_technician_performance_technician_id'), 'reporting_technician_performance', ['technician_id'], unique=False)

    op.create_table(
        'reporting_critical_stock',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False),
        sa.Column('minimum_required', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(length=50), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_critical_stock_asset_type_id'), 'reporting_critical_stock', ['asset_type_id'], unique=False)

    op.create_table(
        'reporting_expiring_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nomenclature', sa.String(length=240), nullable=False),
        sa.Column('remaining_hours', sa.Float(), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_expiring_components_asset_id'), 'reporting_expiring_components', ['asset_id'], unique=False)


def downgrade() -> None:
    op.drop_table('reporting_expiring_components')
    op.drop_table('reporting_critical_stock')
    op.drop_table('reporting_technician_performance')
    op.drop_table('reporting_section_repair_times')
    op.drop_table('reporting_mttr')
    op.drop_table('reporting_mtbf')
    op.drop_table('reporting_fleet_availability')
    op.drop_table('squadron_aircraft_configuration_snapshots')
    op.drop_table('engine_hot_section_inspections')
    op.drop_table('engine_oil_analysis_records')
    op.drop_table('engine_trend_monitoring')
    op.drop_table('engine_cycle_counters')
    op.drop_table('engine_inspection_programs')
    op.drop_table('engine_submodules')
    op.drop_table('engine_assemblies')
    op.drop_table('supply_chain_stock_movement_history')
    
    op.drop_column('supply_chain_stock_items', 'department_id')
    op.drop_column('supply_chain_stock_items', 'military_unit_id')
    op.drop_column('supply_chain_stock_items', 'organization_id')
    op.drop_column('supply_chain_stock_items', 'serialized_inventory')
    op.drop_column('supply_chain_stock_items', 'lot_number')
    op.drop_column('supply_chain_stock_items', 'batch_number')
    op.drop_column('supply_chain_stock_items', 'serial_number')
