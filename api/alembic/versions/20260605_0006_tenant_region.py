"""tenant region residency pinning

Revision ID: 20260605_0006
Revises: 20260605_0005
Create Date: 2026-06-05 00:06:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260605_0006'
down_revision = '20260605_0005'
branch_labels = None
depends_on = None

# gemini-3-flash-preview
def _guarded(conn, fn):
    """Run a DDL callable inside a SAVEPOINT so a failure can't poison the outer txn."""
    try:
        with conn.begin_nested():
            fn()
    except Exception:
        pass

# gemini-3-flash-preview
def upgrade():
    conn = op.get_bind()
    
    # Check if saas_subscription table exists
    res = conn.execute(sa.text("SELECT to_regclass('saas_subscription')")).scalar()
    if res:
        # Check if region column already exists
        col_exists = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'saas_subscription' AND column_name = 'region'"
            )
        ).fetchone()
        
        if not col_exists:
            _guarded(conn, lambda: op.add_column(
                'saas_subscription', 
                sa.Column('region', sa.String(length=20), nullable=True, server_default='sea')
            ))


def downgrade():
    conn = op.get_bind()
    _guarded(conn, lambda: op.drop_column('saas_subscription', 'region'))
