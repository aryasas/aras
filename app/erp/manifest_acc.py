# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_acc.models.account import AccAccount
from app.erp.erp_acc.models import (
    AccJournalEntry, AccJournalLine,
    AccAnalyticTag,
    SalesOrder, SalesOrderLine, SalesOrderCharge,
    AccSalesInvoice, AccSalesInvoiceLine, AccSalesInvoiceCharge,
    AccPurchaseInvoice, AccPurchaseInvoiceLine, AccPurchaseInvoiceCharge,
    AccPayment, AccPaymentAllocation,
)

class JournalEntryHandler(ArasGen.Handler):
    def list(self, query):
        return query.filter_by(state="draft")

    def before_delete(self, obj):
        if getattr(obj, "state", "draft") == "posted":
            raise ValueError("Journal entry yang sudah diposting tidak bisa dihapus.")

class PostableInvoiceHandler(ArasGen.Handler):
    """Handler untuk Sales/Purchase Invoice — inject post_url ke form context."""
    def __init__(self, post_url: str):
        self._post_url = post_url

    def detail_context(self, obj):
        if not obj:
            return {}
        state = getattr(obj, "state", None)

        from arasCore.lib.services.workflow import get_workflow, get_available_actions
        from flask_login import current_user

        cls_name = obj.__class__.__name__
        res_key = None
        if cls_name == "AccSalesInvoice":
            res_key = "erp/acc/sales-invoice"
        elif cls_name == "AccPurchaseInvoice":
            res_key = "erp/acc/purchase-invoice"

        if res_key:
            wf = get_workflow(res_key)
            if wf:
                actions = get_available_actions(current_user, obj, wf)
                return {
                    "obj_state": state,
                    "workflow_actions": actions,
                    "workflow_resource_key": res_key,
                    "obj_id": obj.id
                }

        if state == "draft":
            return {"post_url": self._post_url, "obj_id": obj.id}
        return {"obj_state": state}

class SalesOrderHandler(ArasGen.Handler):
    def detail_context(self, obj):
        if not obj:
            return {}
        if obj.state == "confirmed":
            return {
                "post_url": "/api/erp/acc/sales-order/create-invoice/",
                "obj_id":   obj.id,
            }
        return {"obj_state": obj.state}

class PaymentHandler(ArasGen.Handler):
    def column_setup(self):
        return {
            "partner_id": {
                "field_type": "relation",
                "depend_on_another_field": "partner_type",
                "choices": "customer:crm/customer, supplier:sup/supplier",
                "required": True
            }
        }

    def detail_context(self, obj):
        if not obj:
            return {}
        return {"obj_id": obj.id, "obj_state": obj.state}

    def child_table_actions(self, child_model_name, parent_obj):
        if child_model_name != "acc_payment_allocation":
            return []
        return [
            {
                "id":      "btnLoadInvoices",
                "label":   "Load Invoices",
                "icon":    "fa-refresh",
                "style":   "aras-btn--outline",
                "url":     "/api/erp/acc/payment/load-invoices/",
            },
            {
                "id":      "btnAutoAllocate",
                "label":   "Auto Allocate",
                "icon":    "fa-magic",
                "style":   "aras-btn--lead",
                "url":     "/api/erp/acc/payment/auto-allocate/",
                "confirm": "Auto-allocate payment to unpaid invoices (FIFO)?",
            },
        ]

def _handle_post_journal():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    entry_id = data.get("entry_id")
    if not entry_id:
        return jsonify({"ok": False, "error": "entry_id required"}), 400
    obj = AccJournalEntry.get_or_404(entry_id)
    if getattr(obj, "state", "draft") == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    obj.set_field("state", "posted")
    return jsonify({"ok": True, "data": {"id": obj.id, "state": obj.state}})

def _handle_sales_invoice_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    from app.erp.erp_acc.models.invoice import AccSalesInvoice
    data       = request.get_json() or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return jsonify({"ok": False, "error": "invoice_id required"}), 400
    inv = AccSalesInvoice.get_or_404(invoice_id)
    if inv.state == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    try:
        from app.erp.erp_acc.services.posting import post_sales_invoice
        post_sales_invoice(invoice_id)
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_purchase_invoice_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    from app.erp.erp_acc.models.invoice import AccPurchaseInvoice
    data       = request.get_json() or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return jsonify({"ok": False, "error": "invoice_id required"}), 400
    inv = AccPurchaseInvoice.get_or_404(invoice_id)
    if inv.state == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    try:
        from app.erp.erp_acc.services.purchase_posting import post_purchase_invoice
        post_purchase_invoice(invoice_id)
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_sales_order_confirm():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from app.erp.erp_acc.services.sales_order_service import confirm_order
        confirm_order(int(order_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_sales_order_create_invoice():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from app.erp.erp_acc.services.sales_order_service import create_invoice_from_order
        inv = create_invoice_from_order(int(order_id))
        return jsonify({"ok": True, "invoice_id": inv.id, "invoice_name": inv.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_payment_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    payment_id = data.get("payment_id") or data.get("obj_id")
    if not payment_id:
        return jsonify({"ok": False, "error": "payment_id required"}), 400
    try:
        from app.erp.erp_acc.services.payment_service import post_payment
        post_payment(int(payment_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_payment_allocate():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    payment_id   = data.get("payment_id")
    invoice_type = data.get("invoice_type")
    invoice_id   = data.get("invoice_id")
    amount       = data.get("amount")
    if not all([payment_id, invoice_type, invoice_id, amount]):
        return jsonify({"ok": False, "error": "payment_id, invoice_type, invoice_id, amount required"}), 400
    try:
        from app.erp.erp_acc.services.payment_service import allocate
        alloc = allocate(int(payment_id), invoice_type, int(invoice_id), float(amount))
        return jsonify({"ok": True, "allocation_id": alloc.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_payment_load_invoices():
    from flask import request, jsonify
    data = request.get_json() or {}
    payment_id = data.get("payment_id") or data.get("obj_id")
    
    partner_id   = data.get("partner_id")
    partner_type = data.get("partner_type")
    total_amount = data.get("total_amount", 0)

    try:
        from app.erp.erp_acc.models.payment import AccPayment
        from app.erp.erp_acc.services.payment_service import get_unpaid_invoices
        
        if payment_id:
            payment  = AccPayment.get_or_404(int(payment_id))
            partner_id = payment.partner_id
            partner_type = payment.partner_type
            total_pay = float(payment.total_amount)
            remaining = float(payment.unallocated_amount) if float(payment.unallocated_amount) > 0 else total_pay
        else:
            if not partner_id or not partner_type:
                return jsonify({"ok": False, "error": "partner_id and partner_type required for new payments"}), 400
            
            pay_type = "inbound" if partner_type == "customer" else "outbound"
            payment = AccPayment(partner_id=int(partner_id), partner_type=partner_type, payment_type=pay_type)
            total_pay = float(total_amount)
            remaining = total_pay

        invoices = get_unpaid_invoices(payment)
        allocs = []
        for inv in invoices:
            suggested = min(inv["amount_due"], remaining)
            remaining = max(0.0, remaining - suggested)
            allocs.append({
                "invoice_type": inv["invoice_type"],
                "invoice_id":   inv["invoice_id"],
                "name":         inv["name"],
                "amount":       suggested,
                "notes":        f"Auto-loaded from {inv['name']}"
            })
        
        return jsonify({
            "ok": True, 
            "allocations": allocs, 
            "payment_id": int(payment_id) if payment_id else None,
            "message": f"Found {len(allocs)} unpaid invoice(s)." if allocs else "No unpaid invoices found."
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_payment_auto_allocate():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    payment_id = data.get("payment_id") or data.get("obj_id")
    if not payment_id:
        return jsonify({"ok": False, "error": "payment_id required"}), 400
    try:
        from app.erp.erp_acc.services.payment_service import auto_allocate
        allocs = auto_allocate(int(payment_id))
        return jsonify({"ok": True, "reload": True, "message": f"Allocated {len(allocs)} invoice(s).",
                        "count": len(allocs)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Workflow Event Listeners ──────────────────────────────────────────────────

def register_erp_workflow_listeners():
    from arasCore.lib.core.events import listener
    from app.erp.erp_acc.services.posting import post_sales_invoice
    from app.erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from arasCore.lib.core.extensions import db

    @listener("erp/acc/sales-invoice.state_changed")
    def on_sales_invoice_state_changed(obj, to_state, **kwargs):
        if to_state == "posted":
            try:
                post_sales_invoice(obj.id)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

    @listener("erp/acc/purchase-invoice.state_changed")
    def on_purchase_invoice_state_changed(obj, to_state, **kwargs):
        if to_state == "posted":
            try:
                post_purchase_invoice(obj.id)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

register_erp_workflow_listeners()

def register_invoice_workflows():
    from arasCore.lib.services.workflow import WorkflowDef, TransitionDef, register_workflow
    
    wf_sales = WorkflowDef(
        name="Sales Invoice Workflow",
        resource_key="erp/acc/sales-invoice",
        states=["draft", "submitted", "posted", "cancelled"],
        initial="draft",
        transitions=[
            TransitionDef("submit",    "draft",     "submitted", roles=["accountant"]),
            TransitionDef("post",      "submitted", "posted",    roles=["manager"]),
            TransitionDef("cancel",    ["draft", "submitted"], "cancelled", roles=["manager"]),
        ]
    )
    register_workflow(wf_sales)

    wf_pur = WorkflowDef(
        name="Purchase Invoice Workflow",
        resource_key="erp/acc/purchase-invoice",
        states=["draft", "submitted", "posted", "cancelled"],
        initial="draft",
        transitions=[
            TransitionDef("submit",    "draft",     "submitted", roles=["accountant"]),
            TransitionDef("post",      "submitted", "posted",    roles=["manager"]),
            TransitionDef("cancel",    ["draft", "submitted"], "cancelled", roles=["manager"]),
        ]
    )
    register_workflow(wf_pur)

register_invoice_workflows()

menu_groups = [
    ArasGen.Menu("Accounting", "fa-calculator", order=1, resources=[
        ArasGen.Resource("acc/account",      AccAccount,       admin_list=True,
                    menu_title="Chart of Accounts", menu_icon="fa-sitemap"),
        ArasGen.Resource("acc/entry",        AccJournalEntry,  handler=JournalEntryHandler(), admin_list=True,
                    menu_title="Journal Entries", menu_icon="fa-pencil-square-o"),
        ArasGen.Resource("acc/line",         AccJournalLine,   admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/analytic-tag", AccAnalyticTag,   admin_list=True,
                    menu_title="Analytic Tags", menu_icon="fa-tag"),
        ArasGen.Resource("acc/sales-order",        SalesOrder,       admin_list=True,
                    handler=SalesOrderHandler(),
                    menu_title="Sales Orders", menu_icon="fa-file-text"),
        ArasGen.Resource("acc/sales-order-line",   SalesOrderLine,   admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/sales-order-charge", SalesOrderCharge, admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/sales-invoice",          AccSalesInvoice,        admin_list=True,
                    handler=PostableInvoiceHandler("/api/erp/acc/sales-invoice/post/"),
                    menu_title="Sales Invoices", menu_icon="fa-file-text-o"),
        ArasGen.Resource("acc/sales-invoice-line",     AccSalesInvoiceLine,    admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/sales-invoice-charge",   AccSalesInvoiceCharge,  admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/purchase-invoice",       AccPurchaseInvoice,     admin_list=True,
                    handler=PostableInvoiceHandler("/api/erp/acc/purchase-invoice/post/"),
                    menu_title="Purchase Invoices", menu_icon="fa-file-o"),
        ArasGen.Resource("acc/purchase-invoice-line",  AccPurchaseInvoiceLine, admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/purchase-invoice-charge",AccPurchaseInvoiceCharge,admin_list=False, is_child_table=True),
        ArasGen.Resource("acc/payment",            AccPayment,           admin_list=True,
                    handler=PaymentHandler(),
                    menu_title="Payments", menu_icon="fa-money"),
        ArasGen.Resource("acc/payment-allocation", AccPaymentAllocation, admin_list=False, is_child_table=True),
    ])
]

custom_routes = [
    ArasGen.Route("/acc/entry/post",                          _handle_post_journal,                   methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/sales-invoice/post",                  _handle_sales_invoice_post,             methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/purchase-invoice/post",               _handle_purchase_invoice_post,          methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/sales-order/confirm",                 _handle_sales_order_confirm,            methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/sales-order/create-invoice",          _handle_sales_order_create_invoice,     methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/payment/post",                        _handle_payment_post,                   methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/payment/allocate",                    _handle_payment_allocate,               methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/payment/load-invoices",               _handle_payment_load_invoices,          methods=["POST"], require_auth=True),
    ArasGen.Route("/acc/payment/auto-allocate",               _handle_payment_auto_allocate,          methods=["POST"], require_auth=True),
]

settings_schema = [
    {"key": "account_revenue_default",  "label": "Default Revenue Account (ID)",  "value_type": "integer", "default": None, "order": 8},
    {"key": "account_purchase_default", "label": "Default Purchase Account (ID)", "value_type": "integer", "default": None, "order": 9},
    {"key": "account_cogs_default",     "label": "Default COGS Account (ID)",     "value_type": "integer", "default": None, "order": 9},
    {"key": "accounting_mode_hpp",      "label": "Use COGS (HPP) Accounting Mode","value_type": "boolean", "default": False, "order": 9},
]