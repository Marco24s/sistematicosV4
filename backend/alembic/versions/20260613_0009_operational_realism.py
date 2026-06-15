"""Add operational realism models (AOG, Deferred Defects, Slots, Calibration, Physical Documents, External Repairs, Classification)

Revision ID: 20260613_0009
Revises: 20260613_0008
Create Date: 2026-06-13 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260613_0009'
down_revision: Union[str, None] = '20260613_0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modificar tabla assets (Clasificación e Intercambiabilidad)
    op.add_column('assets', sa.Column('classification', sa.Enum('REPAIRABLE', 'CONSUMABLE', 'ROTABLE', 'CALIBRATION_CONTROLLED', 'LIFE_LIMITED', 'DISPOSABLE', name='asset_classification'), nullable=False, server_default='REPAIRABLE'))
    op.add_column('assets', sa.Column('interchangeability_group', sa.String(length=120), nullable=True))
    op.add_column('assets', sa.Column('batch_number', sa.String(length=120), nullable=True))
    op.add_column('assets', sa.Column('manufacturer_code', sa.String(length=120), nullable=True))
    op.add_column('assets', sa.Column('compatible_platforms', sa.Text(), nullable=True))

    # 2. Modificar tabla work_orders
    op.add_column('work_orders', sa.Column('priority_level', sa.String(length=50), nullable=False, server_default='NORMAL'))
    op.add_column('work_orders', sa.Column('priority_reason', sa.Text(), nullable=True))
    op.add_column('work_orders', sa.Column('requested_deadline', sa.Date(), nullable=True))

    # 3. Tabla: asset_configuration_nodes
    op.create_table(
        'asset_configuration_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_code', sa.String(length=80), nullable=False),
        sa.Column('installation_level', sa.Integer(), nullable=False),
        sa.Column('installed_at', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['parent_asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['child_asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('child_asset_id')
    )
    op.create_index(op.f('ix_asset_configuration_nodes_parent_asset_id'), 'asset_configuration_nodes', ['parent_asset_id'], unique=False)
    op.create_index(op.f('ix_asset_configuration_nodes_child_asset_id'), 'asset_configuration_nodes', ['child_asset_id'], unique=True)

    # 4. Tabla: asset_lifecycle_events
    op.create_table(
        'asset_lifecycle_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('recorded_at', sa.Date(), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor', sa.String(length=180), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_lifecycle_events_asset_id'), 'asset_lifecycle_events', ['asset_id'], unique=False)

    # 5. Tablas del módulo: tool_calibration
    op.create_table(
        'tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_serial', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tool_serial')
    )
    op.create_index(op.f('ix_tools_tool_serial'), 'tools', ['tool_serial'], unique=True)

    op.create_table(
        'calibration_certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('calibration_due_date', sa.Date(), nullable=False),
        sa.Column('certification_document_code', sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calibration_certificates_calibration_due_date'), 'calibration_certificates', ['calibration_due_date'], unique=False)
    op.create_index(op.f('ix_calibration_certificates_tool_id'), 'calibration_certificates', ['tool_id'], unique=False)

    op.create_table(
        'tool_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to_section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_assignments_assigned_to_section_id'), 'tool_assignments', ['assigned_to_section_id'], unique=False)
    op.create_index(op.f('ix_tool_assignments_tool_id'), 'tool_assignments', ['tool_id'], unique=False)

    # 6. Tabla: document_management_physical_custody
    op.create_table(
        'document_management_physical_custody',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_department_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transferred_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transferred_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('received_by', sa.String(length=180), nullable=False),
        sa.Column('released_by', sa.String(length=180), nullable=False),
        sa.Column('transfer_date', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document_management_asset_documents.id'], ),
        sa.ForeignKeyConstraint(['current_department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['transferred_from_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['transferred_to_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_management_physical_custody_document_id'), 'document_management_physical_custody', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_management_physical_custody_current_department_id'), 'document_management_physical_custody', ['current_department_id'], unique=False)

    # 7. Tabla: deferred_defects
    op.create_table(
        'deferred_defects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('failure_report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('allowed_until_hours', sa.Integer(), nullable=True),
        sa.Column('allowed_until_date', sa.Date(), nullable=True),
        sa.Column('restriction_level', sa.String(length=120), nullable=False),
        sa.Column('repair_deadline', sa.Date(), nullable=False),
        sa.Column('approved_by', sa.String(length=180), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['failure_report_id'], ['failure_reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deferred_defects_aircraft_id'), 'deferred_defects', ['aircraft_id'], unique=False)
    op.create_index(op.f('ix_deferred_defects_failure_report_id'), 'deferred_defects', ['failure_report_id'], unique=False)
    op.create_index(op.f('ix_deferred_defects_is_deleted'), 'deferred_defects', ['is_deleted'], unique=False)

    # 8. Tabla: squadron_mounted_component_history
    op.create_table(
        'squadron_mounted_component_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('component_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_code', sa.String(length=80), nullable=False),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('installed_by', sa.String(length=180), nullable=False),
        sa.Column('installed_at_hours', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', sa.String(length=180), nullable=True),
        sa.Column('removed_at_hours', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('hours_consumed_in_position', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['component_asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_squadron_mounted_component_history_aircraft_asset_id'), 'squadron_mounted_component_history', ['aircraft_asset_id'], unique=False)
    op.create_index(op.f('ix_squadron_mounted_component_history_component_asset_id'), 'squadron_mounted_component_history', ['component_asset_id'], unique=False)

    # 9. Tabla: squadron_aircraft_operational_interruptions
    op.create_table(
        'squadron_aircraft_operational_interruptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interruption_type', sa.String(length=80), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['aircraft_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_squadron_aircraft_operational_interruptions_aircraft_id'), 'squadron_aircraft_operational_interruptions', ['aircraft_id'], unique=False)

    # 10. Tabla: squadron_configuration_slots
    op.create_table(
        'squadron_configuration_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aircraft_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slot_code', sa.String(length=80), nullable=False),
        sa.Column('slot_name', sa.String(length=120), nullable=False),
        sa.Column('compatible_asset_types', sa.Text(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('criticality_level', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_squadron_configuration_slots_aircraft_model_id'), 'squadron_configuration_slots', ['aircraft_model_id'], unique=False)
    op.create_index(op.f('ix_squadron_configuration_slots_slot_code'), 'squadron_configuration_slots', ['slot_code'], unique=False)

    # 11. Tablas del módulo: external_repairs
    op.create_table(
        'arsenal_external_repair_vendors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'arsenal_external_repair_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expected_return_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['arsenal_external_repair_vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_arsenal_external_repair_orders_asset_id'), 'arsenal_external_repair_orders', ['asset_id'], unique=False)
    op.create_index(op.f('ix_arsenal_external_repair_orders_vendor_id'), 'arsenal_external_repair_orders', ['vendor_id'], unique=False)


def downgrade() -> None:
    op.drop_table('arsenal_external_repair_orders')
    op.drop_table('arsenal_external_repair_vendors')
    op.drop_table('squadron_configuration_slots')
    op.drop_table('squadron_aircraft_operational_interruptions')
    op.drop_table('squadron_mounted_component_history')
    op.drop_table('deferred_defects')
    op.drop_table('document_management_physical_custody')
    op.drop_table('tool_assignments')
    op.drop_table('calibration_certificates')
    op.drop_table('tools')
    op.drop_table('asset_lifecycle_events')
    op.drop_table('asset_configuration_nodes')
    
    op.drop_column('work_orders', 'requested_deadline')
    op.drop_column('work_orders', 'priority_reason')
    op.drop_column('work_orders', 'priority_level')
    
    op.drop_column('assets', 'compatible_platforms')
    op.drop_column('assets', 'manufacturer_code')
    op.drop_column('assets', 'batch_number')
    op.drop_column('assets', 'interchangeability_group')
    op.drop_column('assets', 'classification')
    sa.Enum(name='asset_classification').drop(op.get_bind(), checkfirst=True)
