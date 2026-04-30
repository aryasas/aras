from arasCore.lib.core.extensions import db
from aras.erp.erp_stock.models.delivery import DeliveryOrder, DeliveryOrderLine, DeliveryTrip
from aras.erp.erp_core.services import sequence as seq_svc


def create_delivery_from_invoice(invoice_id: int) -> DeliveryOrder:
    """Create Delivery Order from a posted Sales Invoice."""
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.get_or_404(invoice_id)
    if inv.state not in ("posted", "partial", "paid"):
        raise ValueError(f"Invoice {inv.name} must be posted before creating delivery.")

    do_name = seq_svc.next_code(inv.company_id, "stock.delivery_order")
    do = DeliveryOrder(
        company_id       = inv.company_id,
        name             = do_name,
        sales_invoice_id = inv.id,
        customer_id      = inv.customer_id,
        src_location_id  = inv.location_id,
    )
    db.session.add(do)
    db.session.flush()

    for line in inv.lines:
        if line.product_id:
            db.session.add(DeliveryOrderLine(
                delivery_id = do.id,
                product_id  = line.product_id,
                description = line.description,
                qty         = line.qty,
                uom_id      = line.uom_id,
            ))

    db.session.commit()
    return do


def create_delivery_from_order(order_id: int) -> DeliveryOrder:
    """Create Delivery Order from a confirmed Sales Order."""
    from aras.erp.erp_acc.models.sales_order import SalesOrder
    order = SalesOrder.get_or_404(order_id)
    if order.state not in ("confirmed", "partial"):
        raise ValueError(f"Order {order.name} must be confirmed before creating delivery.")

    do_name = seq_svc.next_code(order.company_id, "stock.delivery_order")
    do = DeliveryOrder(
        company_id      = order.company_id,
        name            = do_name,
        sales_order_id  = order.id,
        customer_id     = order.customer_id,
        src_location_id = order.location_id,
    )
    db.session.add(do)
    db.session.flush()

    for line in order.lines:
        if line.product_id:
            db.session.add(DeliveryOrderLine(
                delivery_id = do.id,
                product_id  = line.product_id,
                description = line.description,
                qty         = line.qty,
                uom_id      = line.uom_id,
            ))

    db.session.commit()
    return do


def assign_to_trip(delivery_id: int, trip_id: int) -> DeliveryOrder:
    do = DeliveryOrder.get_or_404(delivery_id)
    if do.state not in ("draft", "assigned"):
        raise ValueError(f"Delivery {do.name} cannot be assigned in state {do.state}.")
    do.trip_id = trip_id
    do.state   = "assigned"
    db.session.commit()
    return do


def mark_delivered(delivery_id: int, posted_by_id: int = None) -> DeliveryOrder:
    """Mark delivery as delivered and post stock movement."""
    do = DeliveryOrder.get_or_404(delivery_id)
    if do.state not in ("assigned", "in_transit"):
        raise ValueError(f"Delivery {do.name} is not in transit (state: {do.state}).")

    if do.src_location_id:
        from aras.erp.erp_stock.models.movement import StockMovement, StockMovementLine
        from aras.erp.erp_stock.models.warehouse import StockLocation
        from aras.erp.erp_stock.services.posting import post_movement
        from aras.erp.erp_core.services import sequence as seq_svc

        company_id = do.company_id
        mv_name    = seq_svc.next_code(company_id, "stock.movement")

        # resolve customer virtual location
        cust_loc = StockLocation.find(location_type="customer", company_id=company_id)
        dst_id   = cust_loc.id if cust_loc else None

        mv = StockMovement(
            company_id      = company_id,
            name            = mv_name,
            move_type       = "delivery",
            state           = "confirmed",
            date_move       = db.func.current_date(),
            src_location_id = do.src_location_id,
            dst_location_id = dst_id,
            origin_model    = "stk_delivery_order",
            origin_id       = do.id,
        )
        db.session.add(mv)
        db.session.flush()

        for line in do.lines:
            if line.product_id:
                db.session.add(StockMovementLine(
                    movement_id = mv.id,
                    product_id  = line.product_id,
                    uom_id      = line.uom_id,
                    qty         = line.qty,
                    qty_base    = line.qty,
                ))

        db.session.flush()
        post_movement(mv.id, posted_by_id=posted_by_id, skip_journal=False)

    do.state = "delivered"
    db.session.commit()
    return do
