# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_crm.models import (
    CrmCustomer, CrmContact,
    CrmLead, CrmPipeline, CrmStage, CrmActivity,
)

class CustomerHandler(ArasGen.Handler):
    def detail_context(self, obj):
        if not obj:
            return {}
        try:
            from arasCore.lib.core.extensions import db
            rows = db.session.execute(db.text(
                "SELECT COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0) "
                "FROM acc_journal_line jl "
                "JOIN acc_journal_entry je ON je.id = jl.entry_id "
                "WHERE jl.partner_id = :cid AND jl.partner_type = 'customer' "
                "  AND je.state = 'posted'"
            ), {"cid": obj.id}).fetchone()
            ar_balance = float(rows[0]) if rows and rows[0] else 0.0
            invoices = db.session.execute(db.text(
                "SELECT COUNT(*), COALESCE(SUM(total),0) "
                "FROM acc_sales_invoice WHERE customer_id = :cid AND state != 'cancelled'"
            ), {"cid": obj.id}).fetchone()
            return {"sidebar_cards": [{
                "title": "AR / Customer Balance",
                "rows": [
                    {"label": "Outstanding AR", "value": f"{ar_balance:,.2f}"},
                    {"label": "Total Invoices", "value": str(invoices[0] if invoices else 0)},
                    {"label": "Invoice Total", "value": f"{float(invoices[1] if invoices else 0):,.2f}"},
                ],
            }]}
        except Exception:
            return {}

class LeadHandler(ArasGen.Handler):
    def detail_context(self, obj):
        if not obj or obj.state == "won":
            return {}
        return {"convert_url": "/api/erp/crm/lead/convert-customer/"}

def _handle_lead_convert():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data    = request.get_json() or {}
    lead_id = data.get("lead_id") or data.get("obj_id")
    code    = data.get("customer_code")
    if not lead_id:
        return jsonify({"ok": False, "error": "lead_id required"}), 400
    try:
        from app.erp.erp_crm.services.lead_service import convert_to_customer
        customer = convert_to_customer(int(lead_id), customer_code=code)
        return jsonify({"ok": True, "customer_id": customer.id, "customer_name": customer.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

menu_groups = [
    ArasGen.Menu("CRM", "fa-handshake-o", order=2, resources=[
        ArasGen.Resource("crm/customer",  CrmCustomer,  admin_list=True,
                    handler=CustomerHandler(),
                    menu_title="Customers", menu_icon="fa-user-circle"),
        ArasGen.Resource("crm/contact",   CrmContact,   admin_list=False, is_child_table=True),
        ArasGen.Resource("crm/lead",      CrmLead,      admin_list=True,
                    handler=LeadHandler(),
                    menu_title="Leads", menu_icon="fa-filter"),
        ArasGen.Resource("crm/pipeline",  CrmPipeline,  admin_list=True,
                    menu_title="Pipelines", menu_icon="fa-random"),
        ArasGen.Resource("crm/stage",     CrmStage,     admin_list=False, is_child_table=True),
        ArasGen.Resource("crm/activity",  CrmActivity,  admin_list=False, is_child_table=True),
    ])
]

custom_routes = [
    ArasGen.Route("/crm/lead/convert-customer", _handle_lead_convert, methods=["POST"], require_auth=True),
]

settings_schema = []