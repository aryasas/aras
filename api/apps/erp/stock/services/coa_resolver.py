from typing import Optional
from sqlalchemy.orm import Session
from ..models import Product, ProductCategory
from ...accounting.models import Account
from ...config.models import Company


class CoaResolver:
    """Resolves which GL accounts to use for stock/accounting integration."""

    @staticmethod
    def _get_category(db: Session, product_id: int) -> Optional[ProductCategory]:
        product = db.query(Product).get(product_id)
        if product and product.category_id:
            return db.query(ProductCategory).get(product.category_id)
        return None

    @staticmethod
    def resolve_stock_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        cat = CoaResolver._get_category(db, product_id)
        if cat and cat.account_stock_id:
            return db.get(Account, cat.account_stock_id)
        co = db.get(Company, company_id)
        if co and co.acc_inventory_default_id:
            return db.get(Account, co.acc_inventory_default_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "asset_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_cogs_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        cat = CoaResolver._get_category(db, product_id)
        if cat and cat.account_cogs_id:
            return db.get(Account, cat.account_cogs_id)
        co = db.get(Company, company_id)
        if co and co.acc_cogs_default_id:
            return db.get(Account, co.acc_cogs_default_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "expense_cogs",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_revenue_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        co = db.get(Company, company_id)
        if co and co.acc_income_default_id:
            return db.get(Account, co.acc_income_default_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "income_operating",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ar_account(db: Session, company_id: int) -> Optional[Account]:
        co = db.get(Company, company_id)
        if co and co.acc_receivable_default_id:
            return db.get(Account, co.acc_receivable_default_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "asset_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ap_account(db: Session, company_id: int) -> Optional[Account]:
        co = db.get(Company, company_id)
        if co and co.acc_payable_default_id:
            return db.get(Account, co.acc_payable_default_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "liability_current",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_variance_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        cat = CoaResolver._get_category(db, product_id)
        if cat and cat.account_variance_id:
            return db.get(Account, cat.account_variance_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "expense_cogs",
            Account.is_group == False
        ).first()
