from typing import Any

def recalc_document(doc: Any):
    """
    Shared recalculation logic for Orders and Invoices.
    Calculates subtotal from lines, updates charges (supporting percent/fixed),
    and sets the final total_amount.
    """
    from sqlalchemy.orm import object_session
    db = object_session(doc)
    
    # 1. Calculate Subtotal from lines: qty * (unit_price - discount)
    doc.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in doc.lines)
    
    # 2. Update Charges and calculate total_charge
    total_charge = 0
    for c in doc.charges:
        if db and hasattr(c, 'charge_id') and c.charge_id:
            # Lazy import to avoid circular dependency
            from ...config.models import Charge
            master = db.get(Charge, c.charge_id)
            if master:
                if master.calc_method == "Percent":
                    c.amount = doc.subtotal * (master.rate / 100.0)
                elif master.calc_method == "Fixed":
                    # If it's fixed, we might prefer the master amount if the line amount is 0
                    # or just keep the line amount if it was manually overridden.
                    # For now, we follow the master if it's the standard behavior.
                    if c.amount == 0:
                        c.amount = master.amount
        
        total_charge += c.amount
    
    doc.total_charge = total_charge
    
    # 3. Get Total Tax (defaults to 0 if the model doesn't have it)
    total_tax = getattr(doc, 'total_tax', 0)
    
    # 4. Set Final Total Amount
    doc.total_amount = doc.subtotal + total_tax + doc.total_charge
