"""Create authorization, digital signatures and security audit tables

Revision ID: 20260613_0010
Revises: 20260613_0009
Create Date: 2026-06-13 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260613_0010_auth'
down_revision: Union[str, None] = '20260613_0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla: organization_roles
    op.create_table(
        'organization_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_organization_roles_name'), 'organization_roles', ['name'], unique=True)

    # 2. Tabla: permissions
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # 3. Tabla: role_permission_association (Many-to-Many)
    op.create_table(
        'role_permission_association',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['organization_roles.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 4. Tabla: user_assignments
    op.create_table(
        'user_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['organization_roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_assignments_user_id'), 'user_assignments', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_assignments_organization_id'), 'user_assignments', ['organization_id'], unique=False)
    op.create_index(op.f('ix_user_assignments_department_id'), 'user_assignments', ['department_id'], unique=False)
    op.create_index(op.f('ix_user_assignments_role_id'), 'user_assignments', ['role_id'], unique=False)

    # 5. Tabla: digital_signatures
    op.create_table(
        'digital_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certificate_serial', sa.String(length=120), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('certificate_serial')
    )
    op.create_index(op.f('ix_digital_signatures_user_id'), 'digital_signatures', ['user_id'], unique=False)
    op.create_index(op.f('ix_digital_signatures_certificate_serial'), 'digital_signatures', ['certificate_serial'], unique=True)
    op.create_index(op.f('ix_digital_signatures_expires_at'), 'digital_signatures', ['expires_at'], unique=False)

    # 6. Tabla: security_audit_events
    op.create_table(
        'security_audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('action_attempted', sa.String(length=240), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_audit_events_user_id'), 'security_audit_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_security_audit_events_event_type'), 'security_audit_events', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_table('security_audit_events')
    op.drop_table('digital_signatures')
    op.drop_table('user_assignments')
    op.drop_table('role_permission_association')
    op.drop_table('permissions')
    op.drop_table('organization_roles')
