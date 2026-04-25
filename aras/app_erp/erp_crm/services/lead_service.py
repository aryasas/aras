from datetime import datetime
from arasCore.lib.extensions import db
from aras.app_erp.erp_crm.models import CrmLead, CrmActivity


def convert_to_opportunity(lead_id: int, pipeline_id: int, stage_id: int) -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"type": "opportunity", "pipeline_id": pipeline_id, "stage_id": stage_id})


def mark_won(lead_id: int) -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"state": "won", "date_closed": datetime.utcnow()})


def mark_lost(lead_id: int, reason: str = "") -> CrmLead:
    lead = CrmLead.get_or_404(lead_id)
    return lead.update_self({"state": "lost", "lost_reason": reason, "date_closed": datetime.utcnow()})


def log_activity(lead_id: int, type: str, summary: str,
                 assigned_to_id: int = None, date_due=None,
                 description: str = "", created_by: int = None) -> CrmActivity:
    return CrmActivity.create({
        "lead_id": lead_id, "type": type, "summary": summary,
        "description": description, "date_due": date_due,
        "assigned_to_id": assigned_to_id, "created_by": created_by,
    })


def mark_activity_done(activity_id: int) -> CrmActivity:
    act = CrmActivity.get_or_404(activity_id)
    return act.update_self({"is_done": True, "date_done": datetime.utcnow()})
