"""core_settings_unification

Revision ID: 20260530_0001
Revises: 20260529_0005
Create Date: 2026-05-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260530_0001'
down_revision = '20260529_0005'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Rename table
    op.rename_table('core_sys_settings', 'core_settings')
    
    # 2. Add columns
    op.add_column('core_settings', sa.Column('namespace', sa.String(length=60), nullable=True))
    op.add_column('core_settings', sa.Column('value_type', sa.String(length=20), server_default='str', nullable=True))
    op.add_column('core_settings', sa.Column('is_secret', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('core_settings', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_settings_updated_by', 'core_settings', 'core_users', ['updated_by'], ['id'])
    
    # 3. Migrate data
    op.execute("UPDATE core_settings SET namespace='legacy' WHERE namespace IS NULL")
    
    # 4. Update constraints
    # Try to drop known constraints/indexes by various possible names
    op.execute("ALTER TABLE core_settings DROP CONSTRAINT IF EXISTS core_sys_settings_key_key")
    op.execute("DROP INDEX IF EXISTS ix_core_sys_settings_key")
    
    # Add composite unique
    op.create_unique_constraint('uq_core_settings_namespace_key', 'core_settings', ['namespace', 'key'])
    
    # 5. Make namespace NOT NULL
    op.alter_column('core_settings', 'namespace', nullable=False)
    
    # 6. Follow-up pass: move keys with prefixes
    # 'core.date_format' -> namespace='core', key='date_format'
    op.execute("""
        UPDATE core_settings 
        SET namespace = split_part(key, '.', 1), 
            key = substr(key, strpos(key, '.') + 1)
        WHERE namespace = 'legacy' AND key LIKE '%.%'
    """)

def downgrade():
    # Revert follow-up pass
    op.execute("""
        UPDATE core_settings 
        SET key = namespace || '.' || key
        WHERE namespace != 'legacy'
    """)
    
    op.drop_constraint('uq_core_settings_namespace_key', 'core_settings', type_='unique')
    op.drop_constraint('fk_settings_updated_by', 'core_settings', type_='foreignkey')
    op.drop_column('core_settings', 'updated_by')
    op.drop_column('core_settings', 'is_secret')
    op.drop_column('core_settings', 'value_type')
    op.drop_column('core_settings', 'namespace')
    op.rename_table('core_settings', 'core_sys_settings')
    # op.create_unique_constraint('core_sys_settings_key_key', 'core_sys_settings', ['key'])
