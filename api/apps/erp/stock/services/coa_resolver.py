from typing import Optional
from sqlalchemy.orm import Session
from ..models import Product, ProductCategory
from ...accounting.models import Account


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
            return db.query(Account).get(cat.account_stock_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Asset",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_cogs_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        cat = CoaResolver._get_category(db, product_id)
        if cat and cat.account_cogs_id:
            return db.query(Account).get(cat.account_cogs_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Expense",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_revenue_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Revenue",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ar_account(db: Session, company_id: int) -> Optional[Account]:
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Asset",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_ap_account(db: Session, company_id: int) -> Optional[Account]:
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Liability",
            Account.is_group == False
        ).first()

    @staticmethod
    def resolve_variance_account(db: Session, product_id: int, company_id: int) -> Optional[Account]:
        cat = CoaResolver._get_category(db, product_id)
        if cat and cat.account_variance_id:
            return db.query(Account).get(cat.account_variance_id)
        return db.query(Account).filter(
            Account.company_id == company_id,
            Account.account_type == "Expense",
            Account.is_group == False
        ).first()
