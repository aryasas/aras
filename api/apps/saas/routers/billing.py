# gemini-2-5-flash
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok, err
from core.auth.service import require_admin
from ..models import SaaSInvoice
from typing import List

router = APIRouter(prefix="/billing", tags=["SaaS Billing"])

@router.get("/invoices")
async def list_invoices(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    invoices = db.query(SaaSInvoice).all()
    return ok(invoices)

@router.post("/invoices/{invoice_id}/void")
async def void_invoice(invoice_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    invoice = db.query(SaaSInvoice).get(invoice_id)
    if not invoice:
        return err("Invoice not found")
    invoice.status = "void"
    db.commit()
    return ok(message="Invoice voided")
