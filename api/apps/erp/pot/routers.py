from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from datetime import date
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
    
    items_data = body.get("items", [])
    party_id = body.get("party_id")
    payment_mode_id = body.get("payment_mode_id")
    amount_paid = body.get("amount_paid", 0)
    
    effective_mode = body.get("mode") or session.mode or "sales"
    if effective_mode == "sales":
        invoice_cls = OutflowInvoice
        line_cls = OutflowInvoiceLine
    else:
        invoice_cls = InflowInvoice
        line_cls = InflowInvoiceLine
        
    # Create Invoice
    invoice = invoice_cls(
        org_id=org_id,
        party_id=party_id,
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
            org_id=org_id
        )
        db.add(line)
        total_amount += qty * price
        
    db.flush()
    
    # Call post handlers (workflow)
    from core.logic.handler_registry import HandlerRegistry
    for handler_name in ("post_stock_movement", "post_journal_entry"):
        fn = HandlerRegistry.resolve(handler_name)
        if fn:
            fn(db=db, item=invoice, params={})
            
    invoice.status = "Posted"
    db.flush()
    
    # Create Payment
    if amount_paid > 0:
        # We need an account_id for Payment. For now, try to find from terminal or just use first bank/cash account
        from ..accounting.models import Account
        from sqlalchemy import select
        account_id = db.scalar(select(Account.id).where(Account.org_id == org_id, Account.account_type.in_(["asset_current"])).limit(1))

        payment = Payment(
            org_id=org_id,
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
        
        # Allocate
        alloc = PaymentAllocation(
            payment_id=payment.id,
            invoice_type=invoice_cls.__name__,
            invoice_id=invoice.id,
            amount=min(amount_paid, total_amount),
            org_id=org_id
        )
        db.add(alloc)
        
    db.flush()
    
    return ok({
        "invoice_number": invoice.number,
        "invoice_id": invoice.id,
        "change_amount": max(0, amount_paid - total_amount) if session.mode == "sales" else 0
    })
