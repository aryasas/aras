from typing import Optional
from sqlalchemy.orm import Session

def resolve_account(db: Session, product_id: int, org_id: int, account_type: str) -> Optional[int]:
    """
    Resolve effective account for a product using priority chain:
    product (per-org) → product category → organization default

    account_type: 'income', 'cogs', 'expense'
    """
    from ..models import Item as Product, ItemAccount as ProductAccount, ItemCategory as ProductCategory
    from ...config.models import Organization

    product = db.get(Product, product_id)
    if not product:
        return None

    # 1. Product-level per-org override
    pa = db.query(ProductAccount).filter(
        ProductAccount.item_id == product_id,
        ProductAccount.org_id == org_id
    ).first()
    if pa:
        val = getattr(pa, f"account_{account_type}_id", None)
        if val:
            return val

    # 2. Product category
    if product.category_id:
        cat = db.get(ProductCategory, product.category_id)
        if cat:
            cat_map = {"cogs": "account_cogs_id", "income": None, "expense": None}
            attr = cat_map.get(account_type)
            if attr:
                val = getattr(cat, attr, None)
                if val:
                    return val

    # 3. Organization default
    org = db.get(Organization, org_id)
    if org:
        org_map = {
            "income": "acc_income_default_id",
            "cogs": "acc_cogs_default_id",
            "expense": "acc_cogs_default_id",  # fallback to cogs for expenses
        }
        attr = org_map.get(account_type)
        if attr:
            return getattr(org, attr, None)

    return None
