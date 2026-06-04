from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import date, timedelta

from core.lib.database import get_db
from core.auth.service import get_current_user, require_admin, require_org_access, user_can_access_org
from core.auth.models import User
from core.workspace.models import Organization
from apps.accounting.services.vocabulary import resolve_labels
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


# claude-opus-4-8
def _month_bounds(anchor: date) -> tuple[date, date]:
    start = anchor.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month - timedelta(days=1)


# claude-opus-4-8
def _profit_total(rows: list[dict]) -> float:
    revenue = sum(float(row.get("balance", 0) or 0) for row in rows if row.get("category") == "Revenue")
    expenses = sum(float(row.get("balance", 0) or 0) for row in rows if row.get("category") != "Revenue")
    return revenue - expenses


# claude-opus-4-8
def _recent_documents(db: Session, org_id: int) -> list[dict]:
    from apps.accounting.models import InflowInvoice, OutflowInvoice, Payment
    from apps.party.models import Party

    docs: list[dict] = []
    sales = (
        db.query(InflowInvoice, Party.name.label("party_name"))
        .outerjoin(Party, Party.id == InflowInvoice.party_id)
        .filter(InflowInvoice.org_id == org_id)
        .order_by(InflowInvoice.created_at.desc())
        .limit(5)
        .all()
    )
    purchases = (
        db.query(OutflowInvoice, Party.name.label("party_name"))
        .outerjoin(Party, Party.id == OutflowInvoice.party_id)
        .filter(OutflowInvoice.org_id == org_id)
        .order_by(OutflowInvoice.created_at.desc())
        .limit(5)
        .all()
    )
    payments = (
        db.query(Payment, Party.name.label("party_name"))
        .outerjoin(Party, Party.id == Payment.party_id)
        .filter(Payment.org_id == org_id)
        .order_by(Payment.created_at.desc())
        .limit(5)
        .all()
    )

    for invoice, party_name in sales:
        docs.append(
            {
                "type": "sale",
                "number": invoice.number,
                "status": invoice.status,
                "doc_date": invoice.doc_date,
                "party_name": party_name,
                "amount": float(invoice.total_amount or 0),
                "created_at": invoice.created_at,
            }
        )
    for invoice, party_name in purchases:
        docs.append(
            {
                "type": "purchase",
                "number": invoice.number,
                "status": invoice.status,
                "doc_date": invoice.doc_date,
                "party_name": party_name,
                "amount": float(invoice.total_amount or 0),
                "created_at": invoice.created_at,
            }
        )
    for payment, party_name in payments:
        docs.append(
            {
                "type": "payment",
                "number": payment.number,
                "status": payment.status,
                "doc_date": payment.doc_date,
                "party_name": party_name,
                "amount": float(payment.amount or 0),
                "created_at": payment.created_at,
            }
        )

    docs.sort(key=lambda row: (row["doc_date"] or date.min, row["created_at"]), reverse=True)
    return [{k: v for k, v in row.items() if k != "created_at"} for row in docs[:5]]


# claude-opus-4-8
@router.get("/dashboard")
def get_trade_dashboard(
    request: Request,
    org_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from .services.report_service import _ar_aging, _profit_and_loss, _sales_summary, _stock_summary

    selected_org_id = _selected_org_id(request, db, current_user, org_id)
    today = date.today()
    month_start, month_end = _month_bounds(today)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start, _ = _month_bounds(prev_month_end)
    labels = resolve_labels(db, selected_org_id)

    today_sales_rows = _sales_summary(
        db,
        selected_org_id,
        {"date_from": today.isoformat(), "date_to": today.isoformat()},
        [],
    )["data"]
    month_profit_rows = _profit_and_loss(
        db,
        selected_org_id,
        {"date_from": month_start.isoformat(), "date_to": month_end.isoformat()},
        [],
    )["data"]
    prev_month_profit_rows = _profit_and_loss(
        db,
        selected_org_id,
        {"date_from": prev_month_start.isoformat(), "date_to": prev_month_end.isoformat()},
        [],
    )["data"]
    receivable_rows = _ar_aging(db, selected_org_id, {}, [])["data"]
    stock_rows = _stock_summary(db, selected_org_id, {}, [])["data"]

    today_sales = sum(float(row.get("total", 0) or 0) for row in today_sales_rows)
    month_profit = _profit_total(month_profit_rows)
    prev_month_profit = _profit_total(prev_month_profit_rows)
    if abs(prev_month_profit) <= 0.000001:
        month_profit_change_pct = 0.0 if abs(month_profit) <= 0.000001 else 100.0
    else:
        month_profit_change_pct = ((month_profit - prev_month_profit) / abs(prev_month_profit)) * 100.0

    low_stock_items = [
        {
            "code": row.get("code"),
            "name": row.get("name"),
            "uom": row.get("uom"),
            "balance": float(row.get("balance", 0) or 0),
        }
        for row in stock_rows
        if float(row.get("balance", 0) or 0) <= 0
    ]

    return ok(
        {
            "labels": labels,
            "today_sales": today_sales,
            "month_profit": month_profit,
            "month_profit_change_pct": month_profit_change_pct,
            "receivables_total": sum(float(row.get("outstanding", 0) or 0) for row in receivable_rows),
            "overdue_count": sum(1 for row in receivable_rows if int(row.get("days_outstanding", 0) or 0) > 30),
            "low_stock_count": len(low_stock_items),
            "low_stock_items": low_stock_items[:5],
            "recent_documents": _recent_documents(db, selected_org_id),
        }
    )

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
