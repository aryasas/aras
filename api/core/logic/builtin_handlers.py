"""
Purpose: Built-in workflow side-effect handlers registered at framework startup.
Context: Apps can override any handler by calling HandlerRegistry.register with the same name.
Impact: Powers DB-driven workflow transitions with reusable accounting and stock logic.
"""
from .handler_registry import HandlerRegistry


@HandlerRegistry.register("post_stock_movement", "Create StockMovement lines from document lines")
def post_stock_movement(db, item, params: dict):
    from apps.erp.stock.services.stock import StockComputeService
    from apps.erp.stock.models import StockMovement, StockMovementLine

    move_type = params.get("move_type", "Outgoing")
    location_field = params.get("location_field", "location_id")
    location_id = getattr(item, location_field, None)

    org_id = getattr(item, "org_id", None)
    currency_id = getattr(item, "currency_id", None)
    if not currency_id and org_id:
        from apps.erp.config.models import Organization
        org = db.get(Organization, org_id)
        currency_id = getattr(org, "base_currency_id", None) if org else None

    from core.manager.naming_manager import SeriesManager
    mv_number = SeriesManager.get_next(db, StockMovement.__tablename__)

    movement = StockMovement(
        org_id=org_id,
        currency_id=currency_id,
        number=mv_number,
        move_type=move_type,
        from_location_id=location_id if move_type == "Outgoing" else None,
        to_location_id=location_id if move_type == "Incoming" else None,
        status="Posted",
        notes=f"Auto from {getattr(item, 'number', item.id)}"
    )
    db.add(movement)
    db.flush()

    for line in getattr(item, "lines", []):
        wac = StockComputeService.compute_avg_cost(db, line.product_id)
        db.add(StockMovementLine(
            movement_id=movement.id,
            product_id=line.product_id,
            qty=line.qty,
            uom_id=getattr(line, "uom_id", None),
            unit_cost=wac,
        ))


@HandlerRegistry.register("post_journal_entry", "Post accounting journal entry for document")
def post_journal_entry(db, item, params: dict):
    """
    params:
      mode: "simple" | "cogs"
        simple — 2 lines using account_debit_id + account_credit_id from params
        cogs   — 4 lines: Dr COGS + Cr Inventory (valuation) AND Dr AR + Cr Revenue (sales)
                 uses company default accounts; falls back to product category accounts.
      account_debit_id: int  (simple mode)
      account_credit_id: int (simple mode)
      use_product_category_accounts: bool
    """
    from apps.erp.accounting.services.journal import JournalService
    from apps.erp.stock.services.stock import StockComputeService
    from apps.erp.stock.models import Product, ProductCategory
    from apps.erp.config.models import Organization

    mode = params.get("mode", "simple")
    org_id = getattr(item, "org_id", None)
    org = db.get(Organization, org_id) if org_id else None
    lines = []

    if mode == "simple":
        amount = getattr(item, "total_amount", getattr(item, "amount", 0)) or 0
        debit_id = params.get("account_debit_id") or (org.acc_receivable_default_id if org else None)
        credit_id = params.get("account_credit_id") or (org.acc_income_default_id if org else None)
        if debit_id and credit_id:
            lines = [
                {"account_id": debit_id, "debit": amount, "credit": 0, "description": f"Dr {item.__class__.__name__} {getattr(item, 'number', '')}"},
                {"account_id": credit_id, "debit": 0, "credit": amount, "description": f"Cr {item.__class__.__name__} {getattr(item, 'number', '')}"},
            ]

    elif mode == "cogs":
        use_cat = params.get("use_product_category_accounts", True)
        for line in getattr(item, "lines", []):
            product = db.get(Product, line.product_id) if line.product_id else None
            wac = StockComputeService.compute_avg_cost(db, line.product_id)
            cost_amt = line.qty * wac
            sale_amt = line.qty * getattr(line, "unit_price", 0)

            cogs_id = inv_id = ar_id = rev_id = None
            if use_cat and product and product.category_id:
                cat = db.get(ProductCategory, product.category_id)
                if cat:
                    cogs_id = getattr(cat, "account_cogs_id", None)
                    inv_id = getattr(cat, "account_stock_id", None)

            if org:
                cogs_id = cogs_id or org.acc_cogs_default_id
                inv_id = inv_id or org.acc_inventory_default_id
                ar_id = org.acc_receivable_default_id
                rev_id = org.acc_income_default_id

            if cogs_id and inv_id and cost_amt:
                lines += [
                    {"account_id": cogs_id, "debit": cost_amt, "credit": 0, "description": f"COGS {product.name if product else ''}"},
                    {"account_id": inv_id, "debit": 0, "credit": cost_amt, "description": f"Inventory {product.name if product else ''}"},
                ]
            if ar_id and rev_id and sale_amt:
                lines += [
                    {"account_id": ar_id, "debit": sale_amt, "credit": 0, "description": f"AR {getattr(item, 'number', '')}"},
                    {"account_id": rev_id, "debit": 0, "credit": sale_amt, "description": f"Revenue {getattr(item, 'number', '')}"},
                ]

    if lines:
        JournalService.post_entry(
            db, org_id, lines,
            reference=getattr(item, "number", str(item.id)),
            narrative=f"Auto journal for {item.__class__.__name__} {getattr(item, 'number', '')}",
        )


@HandlerRegistry.register("create_invoice_from_delivery", "Auto-create Sales Invoice from Delivery Note")
def create_invoice_from_delivery(db, item, params: dict):
    from apps.erp.accounting.models import InflowInvoice, InflowInvoiceLine
    from apps.erp.stock.services.price import PriceService

    invoice = InflowInvoice(
        org_id=getattr(item, "org_id", None),
        party_id=getattr(item, "party_id", None) or getattr(item, "customer_id", None),
        status="Draft",
        notes=f"Generated from {getattr(item, 'number', item.id)}",
    )
    db.add(invoice)
    db.flush()

    for line in getattr(item, "lines", []):
        price = PriceService.get_price(db, line.product_id, uom_id=getattr(line, "uom_id", None), qty=line.qty)
        db.add(InflowInvoiceLine(
            invoice_id=invoice.id,
            product_id=line.product_id,
            qty=line.qty,
            uom_id=getattr(line, "uom_id", None),
            unit_price=price,
            discount=0,
            description=f"Ref: {getattr(item, 'number', '')}",
        ))


@HandlerRegistry.register("send_notification", "Send in-app notification to a user or role")
def send_notification(db, item, params: dict):
    from apps.erp.config.models import Notification

    template = params.get("message_template", "Document {number} changed to {status}")
    message = template.format(
        number=getattr(item, "number", ""),
        status=getattr(item, "status", ""),
    )
    user_id = params.get("user_id")
    if user_id:
        db.add(Notification(
            user_id=user_id,
            type="workflow",
            body=message,
            is_read=False,
        ))
