from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import date

from core.lib.database import get_db
from core.auth.service import get_current_user, require_admin, require_org_access, user_can_access_org
from core.auth.models import User
from apps.config.models import Organization
from .services.finance_report_service import FinanceReportService
from .services.report_service import ReportService
from .models import Report
from core.response import ok

router = APIRouter(tags=["Reports"])


def _selected_org_id(request: Request, db: Session, current_user: User, org_id: Optional[int] = None) -> int:
    selected = org_id or getattr(request.state, "org_id", None)
    if not selected:
        raise HTTPException(status_code=400, detail="Organization context required for this report.")
    require_org_access(db, current_user, int(selected))
    return int(selected)


def _report_org_ids(db: Session, current_user: User, org_id: int, consolidated: bool) -> list[int]:
    org_ids = [org_id]
    if consolidated:
        mirrors = db.query(Organization.id).filter_by(coa_source_org_id=org_id).all()
        org_ids += [r.id for r in mirrors if user_can_access_org(db, current_user, r.id)]
    return org_ids

@router.get("/profit-loss")
def get_profit_loss(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    consolidated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = _selected_org_id(request, db, current_user)
    org_ids = _report_org_ids(db, current_user, org_id, consolidated)
    
    return FinanceReportService.get_profit_loss(db, org_ids, date_from, date_to)

@router.get("/balance-sheet")
def get_balance_sheet(
    request: Request,
    date_to: Optional[date] = None,
    consolidated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = _selected_org_id(request, db, current_user)
    org_ids = _report_org_ids(db, current_user, org_id, consolidated)
    
    return FinanceReportService.get_balance_sheet(db, org_ids, date_to)

@router.get("/trial-balance")
def get_trial_balance(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    consolidated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = _selected_org_id(request, db, current_user)
    org_ids = _report_org_ids(db, current_user, org_id, consolidated)

    return FinanceReportService.get_trial_balance(db, org_ids, date_from, date_to)

# claude-sonnet-4-6
@router.post("/seed-all")
def seed_all_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-seed reports for all organizations. Use for prod recovery when orgs are missing reports."""
    from apps.report.seed_reports import run_seed
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
        all_reports = db.query(Report.code, Report.org_id).all()
        detail = f"Report '{report_code}' not found"
        if all_reports:
            detail += f". Available: {[(c, o) for c, o in all_reports[:3]]}"
        else:
            detail += ". No reports in database."
        raise HTTPException(status_code=404, detail=detail)

    filters = {k: v for k, v in request.query_params.items() if v and k not in ('report_code', 'org_id')}
    result = ReportService.generate(report, filters=filters, db=db)
    return ok(result)
