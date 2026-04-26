"""
Sprint C — Deduct stock on arasPos order payment.
Creates a StockMovement (delivery) per POT order, then posts it.
"""
from datetime import date
from decimal import Decimal

from arasCore.lib.extensions import db
from aras.app_erp.erp_pos.models.order import PosOrder
from aras.app_erp.erp_stock.models.movement import StockMovement, StockMovementLine
from aras.app_erp.erp_stock.models.warehouse import StockLocation
from aras.app_erp.erp_stock.services.posting import post_movement
from aras.app_erp.erp_core.services import sequence as seq_svc


def _get_output_location(warehouse_id: int) -> StockLocation | None:
    """Return the output/internal location for a warehouse."""
    return (StockLocation.find(warehouse_id=warehouse_id, location_type="internal", is_active=True)
            or StockLocation.find(warehouse_id=warehouse_id, is_active=True))


def _get_customer_location(company_id: int) -> StockLocation | None:
    return StockLocation.find(warehouse_id=None, location_type="customer", is_active=True)


def deduct_stock_from_order(order_id: int) -> StockMovement | None:
    """
    Create & post a delivery StockMovement for storable products in a POT order.
    Idempotent — if movement already exists (origin), skip.
    Returns None if no storable lines.
    """
    order = PosOrder.get_or_404(order_id)

    existing = StockMovement.find(origin_model="pos_order", origin_id=order.id)
    if existing:
        return existing

    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    terminal = PosTerminal.get(order.session.terminal_id)
    if not terminal:
        return None

    company_id   = terminal.company_id
    warehouse_id = terminal.warehouse_id
    if not warehouse_id:
        return None  # warehouse not configured — skip stock deduction

    src_loc = _get_output_location(warehouse_id)
    dst_loc = _get_customer_location(company_id)
    if not src_loc:
        return None

    # Filter storable lines only
    storable_lines = [
        l for l in order.lines
        if l.product_id and l.product and getattr(l.product, "is_stock_item", True)
    ]
    if not storable_lines:
        return None

    try:
        mv_name = seq_svc.next_number("stock.move", company_id)
    except ValueError:
        mv_name = f"SM/POT/{order.name}"

    mv = StockMovement(
        company_id=company_id,
        name=mv_name,
        move_type="delivery",
        state="confirmed",
        date_move=date.today(),
        src_location_id=src_loc.id,
        dst_location_id=dst_loc.id if dst_loc else None,
        reference=order.name,
        notes=f"arasPos delivery — {order.name}",
        origin_model="pos_order",
        origin_id=order.id,
    )
    db.session.add(mv)
    db.session.flush()

    for line in storable_lines:
        qty      = Decimal(str(line.qty_base)) if line.qty_base else Decimal(str(line.qty))
        uom_id   = line.product.uom_id  # always base UoM for movement
        # Use avg_cost from valuation if available, else 0
        from aras.app_erp.erp_stock.models import StockValuation
        val  = StockValuation.find(product_id=line.product_id, company_id=company_id)
        cost = Decimal(str(val.avg_cost if val else 0))
        db.session.add(StockMovementLine(
            movement_id=mv.id,
            product_id=line.product_id,
            uom_id=uom_id,
            qty=qty,
            qty_base=qty,
            unit_cost=cost,
            total_cost=qty * cost,
        ))

    db.session.flush()
    post_movement(mv.id)
    return mv


def receive_stock_from_order(order_id: int) -> StockMovement | None:
    """
    Outcome mode — buat StockMovement receipt (stok masuk) dari POT order.
    Idempotent via origin_model=pos_order_outcome.
    Hanya storable products.
    """
    order = PosOrder.get_or_404(order_id)

    existing = StockMovement.find(origin_model="pos_order_outcome", origin_id=order.id)
    if existing:
        return existing

    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    terminal = PosTerminal.get(order.session.terminal_id)
    if not terminal:
        return None

    company_id   = terminal.company_id
    warehouse_id = terminal.warehouse_id
    if not warehouse_id:
        return None

    dst_loc = _get_output_location(warehouse_id)  # stok masuk ke internal
    if not dst_loc:
        return None

    # vendor/virtual location as source
    src_loc = (StockLocation.find(warehouse_id=None, location_type="vendor", is_active=True)
               or StockLocation.find(warehouse_id=None, location_type="virtual", is_active=True))

    storable_lines = [
        l for l in order.lines
        if l.product_id and l.product and getattr(l.product, "is_stock_item", True)
    ]
    if not storable_lines:
        return None

    try:
        mv_name = seq_svc.next_number("stock.move", company_id)
    except ValueError:
        mv_name = f"SM/POT-IN/{order.name}"

    mv = StockMovement(
        company_id=company_id,
        name=mv_name,
        move_type="receipt",
        state="confirmed",
        date_move=date.today(),
        src_location_id=src_loc.id if src_loc else None,
        dst_location_id=dst_loc.id,
        reference=order.name,
        notes=f"arasPos outcome (receive) — {order.name}",
        origin_model="pos_order_outcome",
        origin_id=order.id,
    )
    db.session.add(mv)
    db.session.flush()

    for line in storable_lines:
        qty    = Decimal(str(line.qty_base)) if line.qty_base else Decimal(str(line.qty))
        cost   = Decimal(str(line.unit_price or 0))
        db.session.add(StockMovementLine(
            movement_id=mv.id,
            product_id=line.product_id,
            uom_id=line.product.uom_id,
            qty=qty,
            qty_base=qty,
            unit_cost=cost,
            total_cost=qty * cost,
        ))

    db.session.flush()
    post_movement(mv.id)
    return mv
