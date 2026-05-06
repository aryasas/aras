# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_sup.models import (
    SupSupplier,
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge,
)

class PurchaseOrderHandler(ArasGen.Handler):
    def detail_context(self, obj):
        if not obj:
            return {}
        if obj.state == "confirmed":
            return {
                "post_url": "/api/erp/sup/purchase-order/create-invoice/",
                "obj_id":   obj.id,
            }
        return {"obj_state": obj.state}

def _handle_purchase_order_confirm():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from app.erp.erp_sup.services.purchase_order_service import confirm_order
        confirm_order(int(order_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_purchase_order_create_invoice():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from app.erp.erp_sup.services.purchase_order_service import create_invoice_from_order
        inv = create_invoice_from_order(int(order_id))
        return jsonify({"ok": True, "invoice_id": inv.id, "invoice_name": inv.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

menu_groups = [
    ArasGen.Menu("Supplier", "fa-truck", order=3, resources=[
        ArasGen.Resource("sup/supplier",             SupSupplier,         admin_list=True,
                    menu_title="Suppliers", menu_icon="fa-truck"),
        ArasGen.Resource("sup/purchase-order",       PurchaseOrder,       admin_list=True,
                    handler=PurchaseOrderHandler(),
                    menu_title="Purchase Orders", menu_icon="fa-shopping-basket"),
        ArasGen.Resource("sup/purchase-order-line",  PurchaseOrderLine,   admin_list=False, is_child_table=True),
        ArasGen.Resource("sup/purchase-order-charge",PurchaseOrderCharge, admin_list=False, is_child_table=True),
    ])
]

custom_routes = [
    ArasGen.Route("/sup/purchase-order/confirm",              _handle_purchase_order_confirm,         methods=["POST"], require_auth=True),
    ArasGen.Route("/sup/purchase-order/create-invoice",       _handle_purchase_order_create_invoice,  methods=["POST"], require_auth=True),
]

settings_schema = []