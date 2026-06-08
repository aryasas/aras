"""refresh tokens and consent versioning

Revision ID: 20260605_0005
Revises: 20260605_0004
Create Date: 2026-06-05 00:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260605_0005'
down_revision = '20260605_0004'
branch_labels = None
depends_on = None


def upgrade():
    # core_refresh_tokens
    op.create_table(
        'core_refresh_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=256), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['core_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_core_refresh_tokens_token_hash'), 'core_refresh_tokens', ['token_hash'], unique=False)
    op.create_index(op.f('ix_core_refresh_tokens_user_id'), 'core_refresh_tokens', ['user_id'], unique=False)

    # Add consent columns to core_users
    op.add_column('core_users', sa.Column('consent_version', sa.String(length=32), nullable=True))
    op.add_column('core_users', sa.Column('consent_text_hash', sa.String(length=64), nullable=True))

    # Add consent columns to saas_subscription
    op.add_column('saas_subscription', sa.Column('consent_version', sa.String(length=32), nullable=True))
    op.add_column('saas_subscription', sa.Column('consent_text_hash', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('saas_subscription', 'consent_text_hash')
    op.drop_column('saas_subscription', 'consent_version')
    op.drop_column('core_users', 'consent_text_hash')
    op.drop_column('core_users', 'consent_version')
    op.drop_index(op.f('ix_core_refresh_tokens_user_id'), table_name='core_refresh_tokens')
    op.drop_index(op.f('ix_core_refresh_tokens_token_hash'), table_name='core_refresh_tokens')
    op.drop_table('core_refresh_tokens')
