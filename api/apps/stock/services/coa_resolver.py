from typing import Optional
from sqlalchemy.orm import Session
from ..models import Item, ItemCategory, ItemAccount
from apps.accounting.models import Account
from core.workspace.models import Organization
from apps.accounting.services.org_defaults import acc_default


class CoaResolver:
    """Resolves which GL accounts to use for stock/accounting integration."""

    @staticmethod
    def _get_effective_org_id(db: Session, org_id: int) -> int:
        """Returns the org_id that owns the COA for the given org."""
        co = db.get(Organization, org_id)
        if co and co.coa_source_org_id:
            return co.coa_source_org_id
        return org_id

    @staticmethod
    def _get_item_account_field(db: Session, product_id: int, org_id: int, field_name: str) -> Optional[int]:
        """Helper to find an account ID from ItemAccount or ItemCategory."""
        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        
        # 1. Check ItemAccount (item-specific, optionally org-specific)
        acc = db.query(ItemAccount).filter(
            ItemAccount.item_id == product_id,
            (ItemAccount.org_id == effective_org_id) | (ItemAccount.org_id == None)
        ).order_by(ItemAccount.org_id.desc()).first()
        if acc and getattr(acc, field_name, None):
            return getattr(acc, field_name)

        # 2. Check ItemCategory
        product = db.query(Item).get(product_id)
        if product and product.category_id:
            cat = db.query(ItemCategory).get(product.category_id)
            if cat and getattr(cat, field_name, None):
                return getattr(cat, field_name)
        
        return None

    @staticmethod
    def resolve_stock_account(db: Session, product_id: int, org_id: int) -> Optional[Account]:
        # ItemAccount doesn't have account_stock_id, so we use ItemCategory or Org
        product = db.query(Item).get(product_id)
        if product and product.category_id:
            cat = db.query(ItemCategory).get(product.category_id)
            if cat and cat.account_stock_id:
                return db.get(Account, cat.account_stock_id)

        inv_id = acc_default(db, org_id, "acc_inventory_default_id")
        if inv_id:
            return db.get(Account, inv_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type == "asset_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_cogs_account(db: Session, product_id: int, org_id: int) -> Optional[Account]:
        acc_id = CoaResolver._get_item_account_field(db, product_id, org_id, "account_cogs_id")
        if acc_id:
            return db.get(Account, acc_id)

        cogs_id = acc_default(db, org_id, "acc_cogs_default_id")
        if cogs_id:
            return db.get(Account, cogs_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type == "expense_cogs",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_revenue_account(db: Session, product_id: int, org_id: int) -> Optional[Account]:
        acc_id = CoaResolver._get_item_account_field(db, product_id, org_id, "account_income_id")
        if acc_id:
            return db.get(Account, acc_id)

        income_id = acc_default(db, org_id, "acc_income_default_id")
        if income_id:
            return db.get(Account, income_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type == "income_operating",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_expense_account(db: Session, product_id: int, org_id: int) -> Optional[Account]:
        acc_id = CoaResolver._get_item_account_field(db, product_id, org_id, "account_expense_id")
        if acc_id:
            return db.get(Account, acc_id)

        cogs_id = acc_default(db, org_id, "acc_cogs_default_id")
        if cogs_id:
            return db.get(Account, cogs_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type.in_(["expense_operating", "expense_other", "expense_cogs"]),
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ar_account(db: Session, org_id: int) -> Optional[Account]:
        ar_id = acc_default(db, org_id, "acc_receivable_default_id")
        if ar_id:
            return db.get(Account, ar_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type == "asset_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ap_account(db: Session, org_id: int) -> Optional[Account]:
        ap_id = acc_default(db, org_id, "acc_payable_default_id")
        if ap_id:
            return db.get(Account, ap_id)

        effective_org_id = CoaResolver._get_effective_org_id(db, org_id)
        return db.query(Account).filter(
            Account.org_id == effective_org_id,
            Account.account_type == "liability_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_variance_account(db: Session, product_id: int, org_id: int) -> Optional[Account]:
        acc_id = CoaResolver._get_item_account_field(db, product_id, org_id, "account_variance_id")
        if acc_id:
            return db.get(Account, acc_id)

        return db.query(Account).filter(
            Account.org_id == org_id,
            Account.account_type == "expense_cogs",
            Account.is_group == False
        ).first()
