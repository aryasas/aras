from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from apps.config.models import Organization
from .services.finance_report_service import FinanceReportService

router = APIRouter(prefix="/erp/report", tags=["Reports"])

@router.get("/profit-loss")
def get_profit_loss(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    consolidated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = request.state.org_id
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required for this report.")

    org_ids = [org_id]
    if consolidated:
        mirrors = db.query(Organization.id).filter_by(coa_source_org_id=org_id).all()
        org_ids += [r.id for r in mirrors]
    
    return FinanceReportService.get_profit_loss(db, org_ids, date_from, date_to)

@router.get("/balance-sheet")
def get_balance_sheet(
    request: Request,
    date_to: Optional[date] = None,
    consolidated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = request.state.org_id
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required for this report.")

    org_ids = [org_id]
    if consolidated:
        mirrors = db.query(Organization.id).filter_by(coa_source_org_id=org_id).all()
        org_ids += [r.id for r in mirrors]
    
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
    org_id = request.state.org_id
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required for this report.")

    org_ids = [org_id]
    if consolidated:
        mirrors = db.query(Organization.id).filter_by(coa_source_org_id=org_id).all()
        org_ids += [r.id for r in mirrors]
    
    return FinanceReportService.get_trial_balance(db, org_ids, date_from, date_to)
