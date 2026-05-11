# -*- coding: utf-8 -*-
"""ERP workflow event listeners — registered on app boot via manifest.py."""
from arasCore.lib.core.events import listener
from arasCore.lib.core.extensions import db
from app.erp.erp_acc.services.posting import post_sales_invoice
from app.erp.erp_acc.services.purchase_posting import post_purchase_invoice


@listener("erp/acc/sales-invoice.state_changed")
def _on_sales_invoice_state_changed(obj, to_state, **kwargs):
    if to_state == "posted":
        try:
            post_sales_invoice(obj.id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


@listener("erp/acc/purchase-invoice.state_changed")
def _on_purchase_invoice_state_changed(obj, to_state, **kwargs):
    if to_state == "posted":
        try:
            post_purchase_invoice(obj.id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


def register():
    """Idempotent re-registration entrypoint (no-op; listeners are bound at import)."""
    return True
