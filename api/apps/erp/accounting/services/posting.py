from sqlalchemy.orm import Session
from ..models import SalesInvoice, PurchaseInvoice
from .journal import JournalService
from ...stock.services.coa_resolver import CoaResolver


class InvoicePostingService:
    @staticmethod
    def post_sales_invoice(db: Session, invoice: SalesInvoice):
        if invoice.status != "Draft":
            return {"error": f"Invoice is already {invoice.status}"}

        cid = invoice.company_id
        ar_account = CoaResolver.resolve_ar_account(db, cid)
        if not ar_account:
            return {"error": "AR account not found. Please configure a non-group Asset account."}

        lines = [{
            "account_id": ar_account.id,
            "debit": invoice.total_amount,
            "credit": 0,
            "description": f"Sales Invoice {invoice.number}"
        }]

        # Revenue lines — per invoice line product
        for inv_line in invoice.lines:
            rev_account = CoaResolver.resolve_revenue_account(db, inv_line.product_id, cid)
            if not rev_account:
                return {"error": f"Revenue account not found for product {inv_line.product_id}"}
            line_total = inv_line.qty * (inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": rev_account.id,
                "debit": 0,
                "credit": line_total,
                "description": f"Sales Revenue from {invoice.number}"
            })

        # Charge lines
        for charge_line in invoice.charges:
            from ..config.models import Charge
            charge_def = db.query(Charge).get(charge_line.charge_id)
            if charge_def and charge_def.account_collected_id:
                lines.append({
                    "account_id": charge_def.account_collected_id,
                    "debit": 0,
                    "credit": charge_line.amount,
                    "description": f"Charge: {charge_def.name}"
                })
            elif lines:
                # Fallback: add to last revenue line
                lines[-1]["credit"] += charge_line.amount

        try:
            JournalService.post_entry(
                db, cid, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Sales Invoice {invoice.number}"
            )
            invoice.status = "Posted"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return {"error": str(e)}

    @staticmethod
    def post_purchase_invoice(db: Session, invoice: PurchaseInvoice):
        if invoice.status != "Draft":
            return {"error": f"Invoice is already {invoice.status}"}

        cid = invoice.company_id
        ap_account = CoaResolver.resolve_ap_account(db, cid)
        if not ap_account:
            return {"error": "AP account not found. Please configure a non-group Liability account."}

        lines = []

        # Expense lines — per invoice line product
        for inv_line in invoice.lines:
            cogs_account = CoaResolver.resolve_cogs_account(db, inv_line.product_id, cid)
            if not cogs_account:
                return {"error": f"Expense/COGS account not found for product {inv_line.product_id}"}
            line_total = inv_line.qty * (inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": cogs_account.id,
                "debit": line_total,
                "credit": 0,
                "description": f"Purchase Expense from {invoice.number}"
            })

        # Charge lines
        for charge_line in invoice.charges:
            from ..config.models import Charge
            charge_def = db.query(Charge).get(charge_line.charge_id)
            if charge_def and charge_def.account_paid_id:
                lines.append({
                    "account_id": charge_def.account_paid_id,
                    "debit": charge_line.amount,
                    "credit": 0,
                    "description": f"Charge: {charge_def.name}"
                })
            elif lines:
                lines[0]["debit"] += charge_line.amount

        # AP Credit
        lines.append({
            "account_id": ap_account.id,
            "debit": 0,
            "credit": invoice.total_amount,
            "description": f"Purchase Invoice {invoice.number}"
        })

        try:
            JournalService.post_entry(
                db, cid, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Purchase Invoice {invoice.number}"
            )
            invoice.status = "Posted"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
