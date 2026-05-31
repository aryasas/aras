"""account_relations_bridge

Revision ID: 20260530_0002
Revises: 20260530_0001
Create Date: 2026-05-30 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '20260530_0002'
down_revision = '20260530_0001'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'accounting_account_relations' in inspector.get_table_names():
        return
    op.create_table(
        'accounting_account_relations',
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounting_accounts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('related_id', sa.Integer(), sa.ForeignKey('accounting_accounts.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('ix_account_relations_account', 'accounting_account_relations', ['account_id'])
    op.create_index('ix_account_relations_related', 'accounting_account_relations', ['related_id'])


def downgrade():
    op.drop_index('ix_account_relations_related', table_name='accounting_account_relations')
    op.drop_index('ix_account_relations_account', table_name='accounting_account_relations')
    op.drop_table('accounting_account_relations')
