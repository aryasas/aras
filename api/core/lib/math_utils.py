# gemini-flash
"""
ERP calculation helpers.
Standardizes mathematical operations for accounting and stock modules.
"""
from typing import Optional

def line_amount(qty: float, unit_price: float, discount: float = 0.0) -> float:
    """Calculates line amount: qty * (unit_price - discount)"""
    return float(qty * (unit_price - discount))

def line_total(qty: float, unit_price: float, discount: float = 0.0) -> float:
    """Alias for line_amount, ensuring float return."""
    return line_amount(qty, unit_price, discount)

def apply_percent_charge(subtotal: float, rate: float) -> float:
    """Calculates charge based on percentage: subtotal * (rate / 100.0)"""
    return float(subtotal * (rate / 100.0))

# gpt-5
def line_tax(amount: float, rate: Optional[float], inclusive: bool = False) -> float:
    """Calculates line tax from a percentage rate, supporting tax-inclusive prices."""
    if amount is None or rate in (None, 0):
        return 0.0
    if inclusive:
        return round(float(amount - (amount / (1 + (rate / 100.0)))), 10)
    return round(float(amount * (rate / 100.0)), 10)

def invoice_total(subtotal: float, total_tax: float, total_charge: float) -> float:
    """Calculates final invoice total."""
    return float(subtotal + total_tax + total_charge)
