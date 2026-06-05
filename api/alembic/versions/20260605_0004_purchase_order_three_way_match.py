# gpt-5
"""purchase orders and three-way match links

Revision ID: 20260605_0004
Revises: 20260605_0003
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260605_0004"
down_revision = "20260605_0003"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


# gpt-5
def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "accounting_purchase_orders"):
        op.create_table(
            "accounting_purchase_orders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("org_id", sa.Integer(), sa.ForeignKey("core_organizations.id"), nullable=False),
            sa.Column("number", sa.String(length=32), nullable=False),
            sa.Column("doc_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="Draft"),
            sa.Column("note_id", sa.Integer(), sa.ForeignKey("core_notes.id"), nullable=True),
            sa.Column("party_id", sa.Integer(), sa.ForeignKey("party_parties.id"), nullable=False),
            sa.Column("currency_id", sa.Integer(), sa.ForeignKey("core_currencies.id"), nullable=True),
            sa.Column("pricelist_id", sa.Integer(), sa.ForeignKey("config_price_types.id"), nullable=True),
            sa.Column("doc_type", sa.String(length=20), nullable=False, server_default="Order"),
            sa.Column("location_id", sa.Integer(), sa.ForeignKey("stock_locations.id"), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("subtotal", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("total_charge", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("total_amount", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("journal_entry_id", sa.Integer(), sa.ForeignKey("accounting_entries.id"), nullable=True),
            sa.Column("stock_movement_id", sa.Integer(), sa.ForeignKey("stock_movements.id"), nullable=True),
            sa.Column("pos_session_id", sa.Integer(), sa.ForeignKey("pot_sessions.id"), nullable=True),
        )
        op.create_index("ix_accounting_purchase_orders_org_id", "accounting_purchase_orders", ["org_id"])

    if not _table_exists(inspector, "accounting_purchase_order_lines"):
        op.create_table(
            "accounting_purchase_order_lines",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("qty", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("amount", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("accounting_purchase_orders.id"), nullable=False),
            sa.Column("item_id", sa.Integer(), sa.ForeignKey("stock_items.id"), nullable=False),
            sa.Column("uom_id", sa.Integer(), sa.ForeignKey("config_uoms.id"), nullable=True),
            sa.Column("unit_price", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("discount", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("tax_rate_id", sa.Integer(), sa.ForeignKey("accounting_tax_rates.id"), nullable=True),
        )

    if _table_exists(inspector, "accounting_grns"):
        columns = _column_names(inspector, "accounting_grns")
        if "purchase_order_id" not in columns:
            op.add_column("accounting_grns", sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("accounting_purchase_orders.id"), nullable=True))

    if _table_exists(inspector, "accounting_outflow_invoices"):
        columns = _column_names(inspector, "accounting_outflow_invoices")
        if "purchase_order_id" not in columns:
            op.add_column("accounting_outflow_invoices", sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("accounting_purchase_orders.id"), nullable=True))


# gpt-5
def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "accounting_outflow_invoices"):
        columns = _column_names(inspector, "accounting_outflow_invoices")
        if "purchase_order_id" in columns:
            op.drop_column("accounting_outflow_invoices", "purchase_order_id")

    if _table_exists(inspector, "accounting_grns"):
        columns = _column_names(inspector, "accounting_grns")
        if "purchase_order_id" in columns:
            op.drop_column("accounting_grns", "purchase_order_id")

    if _table_exists(inspector, "accounting_purchase_order_lines"):
        op.drop_table("accounting_purchase_order_lines")

    if _table_exists(inspector, "accounting_purchase_orders"):
        op.drop_index("ix_accounting_purchase_orders_org_id", table_name="accounting_purchase_orders")
        op.drop_table("accounting_purchase_orders")
