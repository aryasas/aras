from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from core.lib.database import get_db
from core.auth.service import get_current_user
from core.response import ok, err
from .models import PotSession
from ..stock.models import Item
from ..accounting.models import InflowInvoice, OutflowInvoice, InflowInvoiceLine, OutflowInvoiceLine, Payment, PaymentAllocation

router = APIRouter(prefix="/sessions", tags=["POT"])

def _computed_value(item, name: str, default=0):
    value = getattr(item, name, default)
    return value() if callable(value) else value

def _org_base_currency_id(db: Session, org_id: int):
    from ..config.models import Organization
    org = db.get(Organization, org_id)
    return org.base_currency_id if org else None

def _payment_account_id(db: Session, org_id: int, payment_mode_id: Optional[int]):
    from ..accounting.models import Account
    from ..config.models import Organization, OrganizationPaymentAccount
    from sqlalchemy import select

    if payment_mode_id:
        mapping = db.scalar(
            select(OrganizationPaymentAccount).where(OrganizationPaymentAccount.mode_id == payment_mode_id).limit(1)
        )
        if mapping:
            return mapping.account_id

    org = db.get(Organization, org_id)
    for account_id in (getattr(org, "acc_cash_default_id", None), getattr(org, "acc_bank_default_id", None)):
        if account_id:
            return account_id

    return db.scalar(
        select(Account.id).where(
            Account.org_id == org_id,
            Account.account_type == "asset_current",
            Account.is_group == False,
        ).limit(1)
    )

@router.get("/{session_id}/items")
def get_session_items(session_id: int, mode: str = "", db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    session = db.get(PotSession, session_id)
    if not session:
        return err("Session not found")

    org_id = session.org_id
    effective_mode = mode or session.mode
    from sqlalchemy import select
    stmt = select(Item).where(Item.org_id == org_id)
    if effective_mode == "sales":
        stmt = stmt.where(Item.for_sales == True)
    elif effective_mode == "purchase":
        stmt = stmt.where(Item.for_purchase == True)
    # effective_mode=="both": no filter
    
    items = db.scalars(stmt).all()
    
    result = []
    for item in items:
        # Get price based on mode
        price = _computed_value(item, "default_sale_price" if effective_mode == "sales" else "default_purchase_price", 0)
        result.append({
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "price": price,
            "qty_on_hand": _computed_value(item, "qty_on_hand", 0)
        })
    return ok(result)

@router.post("/{session_id}/quick_invoice")
def quick_invoice(session_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user), body: dict = Body(...)):
    session = db.get(PotSession, session_id)
    if not session: return err("Session not found")
    
    org_id = session.org_id
    user_id = user.id
    currency_id = _org_base_currency_id(db, org_id)
    
    items_data = body.get("items", [])
    party_id = body.get("party_id")
    payment_mode_id = body.get("payment_mode_id")
    amount_paid = body.get("amount_paid", 0)
    
    effective_mode = body.get("mode") or session.mode or "sales"
    if effective_mode == "sales":
        invoice_cls = InflowInvoice
        line_cls = InflowInvoiceLine
    else:
        invoice_cls = OutflowInvoice
        line_cls = OutflowInvoiceLine
        
    # Create Invoice
    invoice = invoice_cls(
        org_id=org_id,
        party_id=party_id,
        currency_id=currency_id,
        pos_session_id=session_id,
        status="Draft",
        doc_date=date.today()
    )
    invoice.save(db, user_id=user_id)
    
    total_amount = 0
    for it in items_data:
        item_id = it["item_id"]
        qty = it["qty"]
        price = it["unit_price"]
        line = line_cls(
            invoice_id=invoice.id,
            item_id=item_id,
            qty=qty,
            unit_price=price,
        )
        db.add(line)
        total_amount += qty * price
        
    db.flush()
    
    from core.logic.handler_registry import HandlerRegistry

    # Stock movement always runs first
    fn = HandlerRegistry.resolve("post_stock_movement")
    if fn:
        fn(db=db, item=invoice, params={})

    # Create Payment first when paid, so combined journal can be linked to it
    payment = None
    if amount_paid > 0:
        if not currency_id:
            return err("Organization base currency is required before creating POS payments")

        account_id = _payment_account_id(db, org_id, payment_mode_id)
        if not account_id:
            return err("Cash/Bank account is required before creating POS payments")

        payment = Payment(
            org_id=org_id,
            currency_id=currency_id,
            payment_type="Incoming" if effective_mode == "sales" else "Outgoing",
            party_type="Customer" if effective_mode == "sales" else "Supplier",
            party_id=party_id,
            account_id=account_id,
            mode_of_payment_id=payment_mode_id,
            amount=amount_paid,
            status="Posted",
            doc_date=date.today()
        )
        payment.save(db, user_id=user_id)

    # Journal: combined DR Cash/CR Revenue when paid, else DR AR/CR Revenue
    fn = HandlerRegistry.resolve("post_journal_entry")
    if fn:
        journal_params = {}
        if payment is not None:
            journal_params["payment_account_id"] = payment.account_id
            journal_params["payment"] = payment
            journal_params["amount_paid"] = amount_paid
        fn(db=db, item=invoice, params=journal_params)

    invoice.status = "Posted"
    db.flush()

    if payment is not None:
        alloc = PaymentAllocation(
            payment_id=payment.id,
            invoice_type=invoice_cls.__name__,
            invoice_id=invoice.id,
            amount=min(amount_paid, total_amount),
        )
        db.add(alloc)
        
    db.flush()
    db.commit()
    db.refresh(invoice)
    
    return ok({
        "invoice_number": invoice.number,
        "invoice_id": invoice.id,
        "change_amount": max(0, amount_paid - total_amount) if effective_mode == "sales" else 0
    })
