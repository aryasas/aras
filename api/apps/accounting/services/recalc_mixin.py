from core import Aras
from core.lib import math_utils
from typing import Any

class DocumentRecalcMixin:
    """
    Mixin for documents that require shared recalculation logic.
    Provides a recalc method and integrates with Aras.on_create/on_update hooks.
    """

    def _recalc_document_logic(self):
        """
        Shared recalculation logic for Orders and Invoices.
        Calculates subtotal from lines, updates charges (supporting percent/fixed),
        and sets the final total_amount.
        """
        db = self.db_session
        
        # 1. Calculate Subtotal from lines: qty * (unit_price - discount)
        for line in self.lines:
            line.amount = math_utils.line_amount(line.qty, line.unit_price, line.discount)
        self.subtotal = sum(line.amount for line in self.lines)
        
        # 2. Update Charges and calculate total_charge
        total_charge = 0
        for c in self.charges:
            if db and hasattr(c, 'charge_id') and c.charge_id:
                # Lazy import to avoid circular dependency
                from plugins.commerce.models import Charge
                master = db.get(Charge, c.charge_id)
                if master:
                    if master.calc_method == "Percent":
                        c.amount = math_utils.apply_percent_charge(self.subtotal, master.rate)
                    elif master.calc_method == "Fixed":
                        # If it's fixed, we might prefer the master amount if the line amount is 0
                        # or just keep the line amount if it was manually overridden.
                        # For now, we follow the master if it's the standard behavior.
                        if c.amount == 0:
                            c.amount = master.amount
            
            total_charge += c.amount
        
        self.total_charge = total_charge
        
        # 3. Get Total Tax (defaults to 0 if the model doesn't have it)
        total_tax = getattr(self, 'total_tax', 0)
        
        # 4. Set Final Total Amount
        self.total_amount = math_utils.invoice_total(self.subtotal, total_tax, self.total_charge)

    def recalc(self):
        """Public method to trigger recalculation."""
        self._recalc_document_logic()

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        """Hook for Aras framework to call recalc on create/update."""
        self.recalc()
