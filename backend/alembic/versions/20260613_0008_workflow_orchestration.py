"""Create event store, command store, and workflow tables

Revision ID: 20260613_0008
Revises: 20260613_0007
Create Date: 2026-06-13 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260613_0008'
down_revision: Union[str, None] = '20260613_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla: domain_event_store
    op.create_table(
        'domain_event_store',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('aggregate_type', sa.String(length=120), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_domain_event_store_event_id'), 'domain_event_store', ['event_id'], unique=True)
    op.create_index(op.f('ix_domain_event_store_aggregate_id'), 'domain_event_store', ['aggregate_id'], unique=False)

    # 2. Tabla: stored_commands
    op.create_table(
        'stored_commands',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('command_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('command_type', sa.String(length=120), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('command_id')
    )
    op.create_index(op.f('ix_stored_commands_command_id'), 'stored_commands', ['command_id'], unique=True)

    # 3. Tabla: workflow_instances
    op.create_table(
        'workflow_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', sa.String(length=80), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_state', sa.String(length=80), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('RUNNING', 'FAILED', 'COMPLETED', 'CANCELED', name='workflow_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_instances_correlation_id'), 'workflow_instances', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_workflow_instances_is_deleted'), 'workflow_instances', ['is_deleted'], unique=False)

    # 4. Tabla: workflow_transition_logs
    op.create_table(
        'workflow_transition_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_state', sa.String(length=80), nullable=False),
        sa.Column('to_state', sa.String(length=80), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('performed_by', sa.String(length=180), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_instance_id'], ['workflow_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_transition_logs_workflow_instance_id'), 'workflow_transition_logs', ['workflow_instance_id'], unique=False)


def downgrade() -> None:
    op.drop_table('workflow_transition_logs')
    op.drop_table('workflow_instances')
    op.drop_table('stored_commands')
    op.drop_table('domain_event_store')
    # Eliminación de enum custom
    sa.Enum(name='workflow_status').drop(op.get_bind(), checkfirst=True)
