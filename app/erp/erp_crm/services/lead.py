from datetime import datetime
from arasCore.lib.core.extensions import db
from app.erp.erp_crm.models import CrmLead, CrmActivity, CrmCustomer
from arasCore.lib.core.action import action


@action()
def convert_to_opportunity(lead_id: int, pipeline_id: int, stage_id: int) -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"type": "opportunity", "pipeline_id": pipeline_id, "stage_id": stage_id})


@action()
def mark_won(lead_id: int) -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"state": "won", "date_closed": datetime.utcnow()})


@action()
def mark_lost(lead_id: int, reason: str = "") -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"state": "lost", "lost_reason": reason, "date_closed": datetime.utcnow()})


@action()
def log_activity(lead_id: int, type: str, summary: str,
                 assigned_to_id: int = None, date_due=None,
                 description: str = "", created_by: int = None) -> CrmActivity:
    return CrmActivity.create({
        "lead_id": lead_id, "type": type, "summary": summary,
        "description": description, "date_due": date_due,
        "assigned_to_id": assigned_to_id, "created_by": created_by,
    })


@action()
def mark_activity_done(activity_id: int) -> CrmActivity:
    act = CrmActivity.get_or_404(activity_id)
    return act.update_self({"is_done": True, "date_done": datetime.utcnow()})


@action()
def convert_to_customer(lead_id: int, customer_code: str = None) -> CrmCustomer:
    """Convert a lead/opportunity into a CrmCustomer. Marks lead as won."""
    lead = CrmLead.get_or_404(lead_id)
    if lead.state == "won" and lead.customer_id:
        return CrmCustomer.get_or_404(lead.customer_id)

    code = customer_code or f"CUST-{lead.id:05d}"

    existing = CrmCustomer.find(company_id=lead.company_id, code=code)
    if existing:
        customer = existing
    else:
        customer = CrmCustomer.create({
            "company_id": lead.company_id,
            "code":       code,
            "name":       lead.name,
            "email":      lead.contact_email,
            "phone":      lead.contact_phone,
        })

    lead.update_self({
        "customer_id": customer.id,
        "state":       "won",
        "date_closed": datetime.utcnow(),
    })
    return customer
