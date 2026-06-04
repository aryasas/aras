# claude-sonnet-4-6
"""
Resolve an organization's default GL/inventory accounts and inventory flags.

The acc_* defaults and inventory flags no longer live on Organization; they live
on accounting.AccountingConfig and stock.StockConfig, read by key via the
AppConfigRegistry. This indirection means consumers (journal posting, COA
resolution, valuation) never reference column locations directly — and apps that
aren't installed simply yield None/defaults instead of an AttributeError.
"""
from typing import Any, Optional
from sqlalchemy.orm import Session
from core.config import AppConfigRegistry


# claude-sonnet-4-6
def acc_default(db: Session, org_id: int, field: str) -> Optional[int]:
    """Return an accounting default account id (e.g. 'acc_income_default_id'),
    or None if accounting isn't installed / unset."""
    cfg = AppConfigRegistry.get(db, "accounting", org_id)
    return getattr(cfg, field, None) if cfg else None


# claude-sonnet-4-6
def stock_default(db: Session, org_id: int, field: str, fallback: Any = None) -> Any:
    """Return a stock config value (account id or flag like
    'stock_valuation_method'/'enable_perpetual_inventory'), or fallback."""
    cfg = AppConfigRegistry.get(db, "stock", org_id)
    if cfg is None:
        return fallback
    val = getattr(cfg, field, None)
    return val if val is not None else fallback
