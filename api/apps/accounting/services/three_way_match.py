# gpt-5
from __future__ import annotations

from collections import defaultdict
from typing import Any


def _aggregate_lines(lines: list[Any], qty_attr: str, price_attr: str) -> dict[int, dict[str, float | list[float]]]:
    buckets: dict[int, dict[str, float | list[float]]] = {}
    for line in lines:
        item_id = int(getattr(line, "item_id"))
        qty = float(getattr(line, qty_attr) or 0)
        price = float(getattr(line, price_attr) or 0)
        entry = buckets.setdefault(item_id, {"qty": 0.0, "prices": []})
        entry["qty"] = float(entry["qty"]) + qty
        prices = entry["prices"]
        assert isinstance(prices, list)
        prices.append(price)
    return buckets


def _validate_single_price(source_name: str, item_id: int, prices: list[float], discrepancies: list[str]) -> float:
    unique_prices = sorted({float(price) for price in prices})
    if len(unique_prices) > 1:
        discrepancies.append(
            f"{source_name} item {item_id}: multiple unit prices found ({', '.join(f'{price:.2f}' for price in unique_prices)})."
        )
    return unique_prices[0] if unique_prices else 0.0


def _qty_diff_exceeds(left: float, right: float, tolerance_pct: float) -> bool:
    baseline = max(abs(right), 1.0)
    allowed = baseline * (tolerance_pct / 100.0)
    return abs(left - right) > allowed


def evaluate_three_way_match(
    *,
    purchase_order: Any,
    goods_receipt: Any,
    invoice: Any,
    qty_tolerance_pct: float,
    price_tolerance_pct: float,
) -> dict[str, Any]:
    # accounting.evaluate_three_way_match
    po_map = _aggregate_lines(list(getattr(purchase_order, "lines", []) or []), "qty", "unit_price")
    grn_map = _aggregate_lines(list(getattr(goods_receipt, "lines", []) or []), "quantity_received", "unit_cost")
    invoice_map = _aggregate_lines(list(getattr(invoice, "lines", []) or []), "qty", "unit_price")

    discrepancies: list[str] = []
    items = sorted(set(po_map) | set(grn_map) | set(invoice_map))

    for item_id in items:
        po_entry = po_map.get(item_id, {"qty": 0.0, "prices": []})
        grn_entry = grn_map.get(item_id, {"qty": 0.0, "prices": []})
        invoice_entry = invoice_map.get(item_id, {"qty": 0.0, "prices": []})

        po_qty = float(po_entry["qty"])
        received_qty = float(grn_entry["qty"])
        invoiced_qty = float(invoice_entry["qty"])

        po_price = _validate_single_price("PO", item_id, list(po_entry["prices"]), discrepancies)
        _validate_single_price("GRN", item_id, list(grn_entry["prices"]), discrepancies)
        invoiced_price = _validate_single_price("Invoice", item_id, list(invoice_entry["prices"]), discrepancies)

        allowed_received_qty = po_qty * (1 + (qty_tolerance_pct / 100.0))
        if received_qty > allowed_received_qty:
            discrepancies.append(
                f"Item {item_id}: received qty {received_qty:.2f} exceeds ordered qty {po_qty:.2f} with tolerance {qty_tolerance_pct:.2f}%."
            )

        if _qty_diff_exceeds(invoiced_qty, received_qty, qty_tolerance_pct):
            discrepancies.append(
                f"Item {item_id}: invoiced qty {invoiced_qty:.2f} differs from received qty {received_qty:.2f} beyond tolerance {qty_tolerance_pct:.2f}%."
            )

        allowed_price = po_price * (1 + (price_tolerance_pct / 100.0))
        if invoiced_price > allowed_price:
            discrepancies.append(
                f"Item {item_id}: invoiced unit price {invoiced_price:.2f} exceeds PO unit price {po_price:.2f} with tolerance {price_tolerance_pct:.2f}%."
            )

    return {"matched": len(discrepancies) == 0, "discrepancies": discrepancies}
