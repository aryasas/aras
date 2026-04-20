"""
COA (Chart of Account) resolver untuk produk.
Urutan prioritas:
  1. Per-product langsung (stock_product.account_*_id)
  2. Per-product + company (stock_product_account_link)
  3. Product category (stock_product_category.account_*_id)
  4. Global setting (erp.account_*_default) — hanya jika erp.accounting_mode_hpp = false
  5. acc_default_account key fallback
"""
from arasCore.lib.extensions import db


def _get_setting(key: str, company_id: int = None):
    """Read from core_setting. company scope checked first, then global."""
    row = None
    if company_id:
        row = db.session.execute(
            db.text("SELECT value, value_type FROM core_setting WHERE scope='company' AND scope_id=:c AND `key`=:k LIMIT 1"),
            {"c": company_id, "k": key}
        ).fetchone()
    if not row:
        row = db.session.execute(
            db.text("SELECT value, value_type FROM core_setting WHERE scope='global' AND `key`=:k LIMIT 1"),
            {"k": key}
        ).fetchone()
    if not row:
        return None
    val, vtype = row
    if vtype == "bool":
        return val.lower() in ("true", "1", "yes")
    if vtype == "int":
        return int(val) if val and val != "0" else None
    return val


def resolve_revenue_account(product, company_id: int):
    """Kembalikan acc_account.id untuk pendapatan, atau None."""
    # 1. Per-product direct
    if getattr(product, "account_revenue_id", None):
        return product.account_revenue_id

    # 2. Per-product + company link
    link = next(
        (l for l in (product.account_links or []) if l.company_id == company_id),
        None
    )
    if link and link.account_revenue_id:
        return link.account_revenue_id

    # 3. Category
    cat = getattr(product, "category", None)
    if cat and cat.account_revenue_id:
        return cat.account_revenue_id

    # 4. Global setting (mode hpp = false → pakai global default)
    hpp_mode = _get_setting("erp.accounting_mode_hpp", company_id)
    if not hpp_mode:
        acc_id = _get_setting("erp.account_revenue_default", company_id)
        if acc_id:
            return acc_id

    # 5. acc_default_account key
    row = db.session.execute(
        db.text("SELECT account_id FROM acc_default_account WHERE company_id=:c AND `key`='income_default' LIMIT 1"),
        {"c": company_id}
    ).fetchone()
    return row[0] if row else None


def resolve_purchase_account(product, company_id: int):
    """Kembalikan acc_account.id untuk pembelian/biaya, atau None."""
    if getattr(product, "account_purchase_id", None):
        return product.account_purchase_id

    link = next(
        (l for l in (product.account_links or []) if l.company_id == company_id),
        None
    )
    if link and link.account_purchase_id:
        return link.account_purchase_id

    cat = getattr(product, "category", None)
    if cat and cat.account_purchase_id:
        return cat.account_purchase_id

    hpp_mode = _get_setting("erp.accounting_mode_hpp", company_id)
    if not hpp_mode:
        acc_id = _get_setting("erp.account_purchase_default", company_id)
        if acc_id:
            return acc_id

    row = db.session.execute(
        db.text("SELECT account_id FROM acc_default_account WHERE company_id=:c AND `key`='purchase_default' LIMIT 1"),
        {"c": company_id}
    ).fetchone()
    return row[0] if row else None


def resolve_cogs_account(product, company_id: int):
    """Kembalikan acc_account.id untuk COGS/HPP, atau None."""
    if getattr(product, "account_cogs_id", None):
        return product.account_cogs_id

    link = next(
        (l for l in (product.account_links or []) if l.company_id == company_id),
        None
    )
    if link and link.account_cogs_id:
        return link.account_cogs_id

    cat = getattr(product, "category", None)
    if cat and cat.account_cogs_id:
        return cat.account_cogs_id

    hpp_mode = _get_setting("erp.accounting_mode_hpp", company_id)
    # Jika mode hpp aktif → selalu pakai global COGS
    acc_id = _get_setting("erp.account_cogs_default", company_id)
    if acc_id:
        return acc_id

    row = db.session.execute(
        db.text("SELECT account_id FROM acc_default_account WHERE company_id=:c AND `key`='cogs_default' LIMIT 1"),
        {"c": company_id}
    ).fetchone()
    return row[0] if row else None
