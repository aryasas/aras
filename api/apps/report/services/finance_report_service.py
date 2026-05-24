from sqlalchemy import func
from sqlalchemy.orm import Session
from core import Aras
from apps.accounting.models import JournalEntry, JournalEntryLine, Account

class FinanceReportService(Aras.Service):
    @staticmethod
    def get_profit_loss(db: Session, org_ids: list[int], date_from=None, date_to=None):
        query = db.query(
            Account.account_type,
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.credit - JournalEntryLine.debit).label("balance")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))\
         .filter(Account.account_type.in_(['income_operating', 'income_other', 'expense_cogs', 'expense_operating', 'expense_other']))
        
        if date_from:
            query = query.filter(JournalEntry.doc_date >= date_from)
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.account_type, Account.name).all()
        
        data = []
        for r in results:
            category = "Other"
            amount = float(r.balance) if r.balance else 0.0
            if r.account_type.startswith("income"):
                category = "Revenue"
            elif r.account_type == "expense_cogs":
                category = "Cost of Goods Sold"
                amount = -amount
            elif r.account_type == "expense_operating":
                category = "Operating Expenses"
                amount = -amount
            elif r.account_type == "expense_other":
                category = "Other Expenses"
                amount = -amount
            
            data.append({
                "category": category,
                "account_name": r.account_name,
                "balance": amount
            })
            
        return {
            "title": "Profit & Loss",
            "data": data,
            "columns": [
                {"field": "category", "label": "Category", "type": "string"},
                {"field": "account_name", "label": "Account", "type": "string"},
                {"field": "balance", "label": "Amount", "type": "currency"},
            ]
        }

    @staticmethod
    def get_balance_sheet(db: Session, org_ids: list[int], date_to=None):
        query = db.query(
            Account.account_type,
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("balance")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))\
         .filter(Account.account_type.in_([
             "asset_current", "asset_fixed", "asset_other",
             "liability_current", "liability_long",
             "equity"
         ]))
        
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.account_type, Account.name).all()
        
        data = []
        for r in results:
            category = "Other"
            amount = float(r.balance) if r.balance else 0.0
            if r.account_type.startswith("asset"):
                category = "Assets"
            elif r.account_type.startswith("liability"):
                category = "Liabilities"
                amount = -amount
            elif r.account_type == "equity":
                category = "Equity"
                amount = -amount
            
            data.append({
                "category": category,
                "account_name": r.account_name,
                "balance": amount
            })
            
        return {
            "title": "Balance Sheet",
            "data": data,
            "columns": [
                {"field": "category", "label": "Category", "type": "string"},
                {"field": "account_name", "label": "Account", "type": "string"},
                {"field": "balance", "label": "Amount", "type": "currency"},
            ]
        }

    @staticmethod
    def get_trial_balance(db: Session, org_ids: list[int], date_from=None, date_to=None):
        query = db.query(
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.debit).label("total_debit"),
            func.sum(JournalEntryLine.credit).label("total_credit")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))
        
        if date_from:
            query = query.filter(JournalEntry.doc_date >= date_from)
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.code, Account.name).order_by(Account.code).all()
        
        data = [
            {
                "account_code": r.account_code,
                "account_name": r.account_name,
                "total_debit": float(r.total_debit) if r.total_debit else 0.0,
                "total_credit": float(r.total_credit) if r.total_credit else 0.0
            } for r in results
        ]
            
        return {
            "title": "Trial Balance",
            "data": data,
            "columns": [
                {"field": "account_code", "label": "Account Code", "type": "string"},
                {"field": "account_name", "label": "Account Name", "type": "string"},
                {"field": "total_debit", "label": "Debit", "type": "currency"},
                {"field": "total_credit", "label": "Credit", "type": "currency"},
            ]
        }
