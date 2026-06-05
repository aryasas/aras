# gpt-5
"""tax engine: tax rates, invoice tax totals, and line tax fields

Revision ID: 20260605_0003
Revises: 20260605_0002
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260605_0003"
down_revision = "20260605_0002"
branch_labels = None
depends_on = None


# gpt-5
def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "accounting_tax_rates" not in existing_tables:
        op.create_table(
            "accounting_tax_rates",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("org_id", sa.Integer(), sa.ForeignKey("core_organizations.id"), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("rate", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_inclusive", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("tax_account_id", sa.Integer(), sa.ForeignKey("accounting_accounts.id"), nullable=True),
        )
        op.create_index("ix_accounting_tax_rates_org_id", "accounting_tax_rates", ["org_id"])
        op.create_index("ix_accounting_tax_rates_is_shared", "accounting_tax_rates", ["is_shared"])

    def ensure_column(table_name, column):
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        if column.name not in existing_cols:
            op.add_column(table_name, column)

    ensure_column("accounting_inflow_invoices", sa.Column("total_tax", sa.Float(), nullable=False, server_default=sa.text("0")))
    ensure_column("accounting_outflow_invoices", sa.Column("total_tax", sa.Float(), nullable=False, server_default=sa.text("0")))
    ensure_column("accounting_inflow_invoice_lines", sa.Column("tax_rate_id", sa.Integer(), sa.ForeignKey("accounting_tax_rates.id"), nullable=True))
    ensure_column("accounting_inflow_invoice_lines", sa.Column("tax_amount", sa.Float(), nullable=False, server_default=sa.text("0")))
    ensure_column("accounting_outflow_invoice_lines", sa.Column("tax_rate_id", sa.Integer(), sa.ForeignKey("accounting_tax_rates.id"), nullable=True))
    ensure_column("accounting_outflow_invoice_lines", sa.Column("tax_amount", sa.Float(), nullable=False, server_default=sa.text("0")))


# gpt-5
def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def drop_column_if_exists(table_name, column_name):
        if table_name not in existing_tables:
            return
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        if column_name in existing_cols:
            op.drop_column(table_name, column_name)

    drop_column_if_exists("accounting_outflow_invoice_lines", "tax_amount")
    drop_column_if_exists("accounting_outflow_invoice_lines", "tax_rate_id")
    drop_column_if_exists("accounting_inflow_invoice_lines", "tax_amount")
    drop_column_if_exists("accounting_inflow_invoice_lines", "tax_rate_id")
    drop_column_if_exists("accounting_outflow_invoices", "total_tax")
    drop_column_if_exists("accounting_inflow_invoices", "total_tax")

    if "accounting_tax_rates" in existing_tables:
        op.drop_index("ix_accounting_tax_rates_is_shared", table_name="accounting_tax_rates")
        op.drop_index("ix_accounting_tax_rates_org_id", table_name="accounting_tax_rates")
        op.drop_table("accounting_tax_rates")
