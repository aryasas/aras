# gemini-2.5-flash
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from core.lib.database import get_db
from core.auth.service import get_current_user, user_can_access_org
from core.auth.models import User
from core.workspace.models import Organization
from core.response import ok
from core.report.routers import _selected_org_id
from ..reports import FinanceReportService, build_trade_dashboard

router = APIRouter(tags=["Accounting Reports"])

# claude-sonnet-4-6
def _report_org_ids(db: Session, current_user: User, org_id: int, consolidated: bool) -> list[int]:
    org_ids = [org_id]
    if consolidated:
        mirrors = db.query(Organization.id).filter_by(coa_source_org_id=org_id).all()
        org_ids += [r.id for r in mirrors if user_can_access_org(db, current_user, r.id)]
    return org_ids

@router.get("/dashboard")
def get_trade_dashboard(
    request: Request,
    org_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    selected_org_id = _selected_org_id(request, db, current_user, org_id)
    result = build_trade_dashboard(db, selected_org_id, current_user)
    return ok(result)

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
