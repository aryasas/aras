from datetime import datetime
from arasCore.lib.extensions import db
from aras.app_erp.erp_crm.models import CrmLead, CrmActivity


def convert_to_opportunity(lead_id: int, pipeline_id: int, stage_id: int) -> CrmLead:
    lead = CrmLead.query.get_or_404(lead_id)
    lead.type        = "opportunity"
    lead.pipeline_id = pipeline_id
    lead.stage_id    = stage_id
    db.session.commit()
    return lead


def mark_won(lead_id: int) -> CrmLead:
    lead = CrmLead.query.get_or_404(lead_id)
    lead.state       = "won"
    lead.date_closed = datetime.utcnow()
    db.session.commit()
    return lead


def mark_lost(lead_id: int, reason: str = "") -> CrmLead:
    lead = CrmLead.query.get_or_404(lead_id)
    lead.state       = "lost"
    lead.lost_reason = reason
    lead.date_closed = datetime.utcnow()
    db.session.commit()
    return lead


def log_activity(lead_id: int, type: str, summary: str,
                 assigned_to_id: int = None, date_due=None,
                 description: str = "", created_by: int = None) -> CrmActivity:
    act = CrmActivity(
        lead_id=lead_id,
        type=type,
        summary=summary,
        description=description,
        date_due=date_due,
        assigned_to_id=assigned_to_id,
        created_by=created_by,
    )
    db.session.add(act)
    db.session.commit()
    return act


def mark_activity_done(activity_id: int) -> CrmActivity:
    act = CrmActivity.query.get_or_404(activity_id)
    act.is_done    = True
    act.date_done  = datetime.utcnow()
    db.session.commit()
    return act
