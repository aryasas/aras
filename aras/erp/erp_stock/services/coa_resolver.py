"""
COA (Chart of Account) resolver for products.
Priority order:
  1. Per-product direct (stock_product.account_*_id)
  2. Per-product + company link (stock_product_account_link)
  3. Product category (stock_product_category.account_*_id)
  4. Global setting (erp.account_*_default) — only if accounting_mode_hpp=false
"""
from arasCore.lib.core.extensions import db


def _company_default(company_id: int, field: str):
    from aras.erp.erp_core.models.company import Company
    c = Company.query.filter_by(id=company_id).first()
    return getattr(c, field, None) if c else None


def _get_setting(key: str, company_id: int = None):
    row = None
    if company_id:
        row = db.session.execute(
            db.text("SELECT value, value_type FROM setting WHERE scope='company' AND scope_id=:c AND `key`=:k LIMIT 1"),
            {"c": company_id, "k": key}
        ).fetchone()
    if not row:
        row = db.session.execute(
            db.text("SELECT value, value_type FROM setting WHERE scope='global' AND `key`=:k LIMIT 1"),
            {"k": key}
        ).fetchone()
    if not row:
        return None
    val, vtype = row
    if vtype in ("bool", "boolean"):
        return val.lower() in ("true", "1", "yes")
    if vtype in ("int", "integer"):
        return int(val) if val and val != "0" else None
    return val


def resolve_revenue_account(product, company_id: int):
    if getattr(product, "account_revenue_id", None):
        return product.account_revenue_id

    link = next((l for l in (product.account_links or []) if l.company_id == company_id), None)
    if link and link.account_revenue_id:
        return link.account_revenue_id

    cat = getattr(product, "category", None)
    if cat and cat.account_revenue_id:
        return cat.account_revenue_id

    if not _get_setting("erp.accounting_mode_hpp", company_id):
        val = _get_setting("erp.account_revenue_default", company_id)
        if val:
            return val
    return _company_default(company_id, "acc_income_default_id")


def resolve_purchase_account(product, company_id: int):
    if getattr(product, "account_purchase_id", None):
        return product.account_purchase_id

    link = next((l for l in (product.account_links or []) if l.company_id == company_id), None)
    if link and link.account_purchase_id:
        return link.account_purchase_id

    cat = getattr(product, "category", None)
    if cat and cat.account_purchase_id:
        return cat.account_purchase_id

    if not _get_setting("erp.accounting_mode_hpp", company_id):
        val = _get_setting("erp.account_purchase_default", company_id)
        if val:
            return val
    return _company_default(company_id, "acc_payable_default_id")


def resolve_cogs_account(product, company_id: int):
    if getattr(product, "account_cogs_id", None):
        return product.account_cogs_id

    link = next((l for l in (product.account_links or []) if l.company_id == company_id), None)
    if link and link.account_cogs_id:
        return link.account_cogs_id

    cat = getattr(product, "category", None)
    if cat and cat.account_cogs_id:
        return cat.account_cogs_id

    val = _get_setting("erp.account_cogs_default", company_id)
    if val:
        return val
    return _company_default(company_id, "acc_cogs_default_id")


def resolve_stock_account(product, company_id: int):
    if getattr(product, "account_stock_id", None):
        return product.account_stock_id

    link = next((l for l in (product.account_links or []) if l.company_id == company_id), None)
    if link and getattr(link, "account_stock_id", None):
        return link.account_stock_id

    cat = getattr(product, "category", None)
    if cat and cat.account_stock_id:
        return cat.account_stock_id

    val = _get_setting("erp.account_stock_default", company_id)
    if val:
        return val
    return _company_default(company_id, "acc_stock_default_id")
