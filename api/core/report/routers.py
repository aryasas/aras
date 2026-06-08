from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from core.lib.database import get_db
from core.auth.service import get_current_user, require_admin, require_org_access
from core.auth.models import User
from .services.report_service import ReportService
from .models import Report
from core.response import ok

router = APIRouter(tags=["Reports"])


# gemini-flash
def _selected_org_id(request: Request, db: Session, current_user: User, org_id: Optional[int] = None) -> int:
    """Generic helper to resolve org_id from request or params and check access."""
    selected = org_id or getattr(request.state, "org_id", None)
    if not selected:
        raise HTTPException(status_code=400, detail="Organization context required for this operation.")
    require_org_access(db, current_user, int(selected))
    return int(selected)


# claude-sonnet-4-6
@router.post("/seed-all")
def seed_all_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-seed reports for all organizations. Use for prod recovery when orgs are missing reports."""
    from core.report.seed_reports import run_seed
    from core.workspace.models import Organization
    deleted = db.query(Report).filter(or_(Report.code.is_(None), Report.code == '')).delete()
    orgs = db.query(Organization).all()

    for org in orgs:
        run_seed(db, org.id)
    db.commit()
    return ok({"seeded_org_ids": [o.id for o in orgs], "orphans_removed": deleted}, f"Reports seeded for {len(orgs)} organization(s).")


# claude-sonnet-4-6
@router.get("/execute/{report_code}")
def execute_report(
    report_code: str,
    org_id: Optional[int] = None,
    request: Request = None,  # type: ignore
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a database-defined report by code within a validated organization context."""
    org_id = _selected_org_id(request, db, current_user, org_id)

    query = db.query(Report).filter(Report.code == report_code, Report.org_id == org_id)

    report = query.first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_code}' not found.")

    filters = {k: v for k, v in request.query_params.items() if v and k not in ('report_code', 'org_id')}
    result = ReportService.generate(report, filters=filters, db=db, current_user=current_user)
    return ok(result)
