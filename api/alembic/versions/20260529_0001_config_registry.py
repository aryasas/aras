"""config_registry

Revision ID: 20260529_0001
Revises: 20260526_0003
Create Date: 2026-05-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260529_0001'
down_revision = '20260526_0003'
branch_labels = None
depends_on = None

def upgrade():
    # config_values
    op.create_table(
        'core_config_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scope_key', sa.String(length=100), nullable=False),
        sa.Column('field_key', sa.String(length=100), nullable=False),
        sa.Column('value_json', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scope_key', 'field_key', name='uq_core_config_values_scope_field')
    )
    
    # config_value_audit
    op.create_table(
        'core_config_value_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scope_key', sa.String(length=100), nullable=True),
        sa.Column('field_key', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ts', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_core_config_value_audit_field_key'), 'core_config_value_audit', ['field_key'], unique=False)
    op.create_index(op.f('ix_core_config_value_audit_scope_key'), 'core_config_value_audit', ['scope_key'], unique=False)

    # audit_log
    op.create_table(
        'core_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('row_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=True),
        sa.Column('diff_json', sa.JSON(), nullable=True),
        sa.Column('ts', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_core_audit_log_action'), 'core_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_core_audit_log_row_id'), 'core_audit_log', ['row_id'], unique=False)
    op.create_index(op.f('ix_core_audit_log_table_name'), 'core_audit_log', ['table_name'], unique=False)
    op.create_index(op.f('ix_core_audit_log_tenant_id'), 'core_audit_log', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_core_audit_log_user_id'), 'core_audit_log', ['user_id'], unique=False)

    # numbering_sequences
    op.create_table(
        'core_numbering_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(length=100), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('last_seq', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_type', 'org_id', 'year', name='uq_core_numbering_sequences_doc_org_year')
    )
    
    # Update core_apps table
    op.add_column('core_apps', sa.Column('required', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('core_apps', sa.Column('provides', sa.JSON(), nullable=True))
    op.add_column('core_apps', sa.Column('config', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('core_apps', 'config')
    op.drop_column('core_apps', 'provides')
    op.drop_column('core_apps', 'required')
    op.drop_table('core_numbering_sequences')
    op.drop_table('core_audit_log')
    op.drop_table('core_config_value_audit')
    op.drop_table('core_config_values')
