# gemini-2.5-flash
from datetime import date, datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from core import Aras
from core.report.services.report_service import ReportService, _parse_date
from apps.accounting.models import JournalEntry, JournalEntryLine, Account, InflowInvoice, OutflowInvoice, Payment, InflowInvoiceLine, OutflowInvoiceLine, TaxRate
from apps.party.models import Party
from apps.accounting.services.vocabulary import resolve_labels
from apps.accounting.config_models import AccountingConfig

# claude-sonnet-4-6
class FinanceReportService(Aras.Service):
    @staticmethod
    def get_profit_loss(db: Session, org_ids: list[int], date_from=None, date_to=None):
        query = db.query(
            Account.account_type,
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.credit - JournalEntryLine.debit).label("balance")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))\
         .filter(Account.account_type.in_(['income_operating', 'income_other', 'expense_cogs', 'expense_operating', 'expense_other']))
        
        if date_from:
            query = query.filter(JournalEntry.doc_date >= date_from)
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.account_type, Account.name).all()
        
        data = []
        for r in results:
            category = "Other"
            amount = float(r.balance) if r.balance else 0.0
            if r.account_type.startswith("income"):
                category = "Revenue"
            elif r.account_type == "expense_cogs":
                category = "Cost of Goods Sold"
                amount = -amount
            elif r.account_type == "expense_operating":
                category = "Operating Expenses"
                amount = -amount
            elif r.account_type == "expense_other":
                category = "Other Expenses"
                amount = -amount
            
            data.append({
                "category": category,
                "account_name": r.account_name,
                "balance": amount
            })
            
        return {
            "title": "Profit & Loss",
            "data": data,
            "columns": [
                {"field": "category", "label": "Category", "type": "string"},
                {"field": "account_name", "label": "Account", "type": "string"},
                {"field": "balance", "label": "Amount", "type": "currency"},
            ]
        }

    @staticmethod
    def get_balance_sheet(db: Session, org_ids: list[int], date_to=None):
        query = db.query(
            Account.account_type,
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("balance")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))\
         .filter(Account.account_type.in_([
             "asset_current", "asset_fixed", "asset_other",
             "liability_current", "liability_long",
             "equity"
         ]))
        
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.account_type, Account.name).all()
        
        data = []
        for r in results:
            category = "Other"
            amount = float(r.balance) if r.balance else 0.0
            if r.account_type.startswith("asset"):
                category = "Assets"
            elif r.account_type.startswith("liability"):
                category = "Liabilities"
                amount = -amount
            elif r.account_type == "equity":
                category = "Equity"
                amount = -amount
            
            data.append({
                "category": category,
                "account_name": r.account_name,
                "balance": amount
            })
            
        return {
            "title": "Balance Sheet",
            "data": data,
            "columns": [
                {"field": "category", "label": "Category", "type": "string"},
                {"field": "account_name", "label": "Account", "type": "string"},
                {"field": "balance", "label": "Amount", "type": "currency"},
            ]
        }

    @staticmethod
    def get_trial_balance(db: Session, org_ids: list[int], date_from=None, date_to=None):
        query = db.query(
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.debit).label("total_debit"),
            func.sum(JournalEntryLine.credit).label("total_credit")
        ).join(JournalEntryLine, JournalEntryLine.account_id == Account.id)\
         .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)\
         .filter(JournalEntry.status == 'Posted')\
         .filter(JournalEntry.org_id.in_(org_ids))
        
        if date_from:
            query = query.filter(JournalEntry.doc_date >= date_from)
        if date_to:
            query = query.filter(JournalEntry.doc_date <= date_to)
            
        results = query.group_by(Account.id, Account.code, Account.name).order_by(Account.code).all()
        
        data = [
            {
                "account_code": r.account_code,
                "account_name": r.account_name,
                "total_debit": float(r.total_debit) if r.total_debit else 0.0,
                "total_credit": float(r.total_credit) if r.total_credit else 0.0
            } for r in results
        ]
            
        return {
            "title": "Trial Balance",
            "data": data,
            "columns": [
                {"field": "account_code", "label": "Account Code", "type": "string"},
                {"field": "account_name", "label": "Account Name", "type": "string"},
                {"field": "total_debit", "label": "Debit", "type": "currency"},
                {"field": "total_credit", "label": "Credit", "type": "currency"},
            ]
        }

# ── Builtin Report Implementations ───────────────────────────────────────────

MAX_REPORT_ROWS = 1000

# claude-sonnet-4-6
@ReportService.register("sales_summary")
def _sales_summary(db: Session, org_id: int, params: dict, columns: list):
    labels = resolve_labels(db, org_id)
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))
    status = params.get("status") or None

    q = (db.query(
            InflowInvoice.number.label("invoice_no"),
            Party.name.label("customer"),
            InflowInvoice.doc_date.label("date"),
            InflowInvoice.subtotal,
            InflowInvoice.total_charge.label("tax"),
            InflowInvoice.total_amount.label("total"),
            InflowInvoice.status,
        )
        .join(Party, Party.id == InflowInvoice.party_id)
        .filter(InflowInvoice.org_id == org_id)
    )
    if date_from:
        q = q.filter(InflowInvoice.doc_date >= date_from)
    if date_to:
        q = q.filter(InflowInvoice.doc_date <= date_to)
    if status:
        q = q.filter(InflowInvoice.status == status)
    q = q.order_by(InflowInvoice.doc_date.desc()).limit(MAX_REPORT_ROWS)

    data = [row._asdict() for row in q.all()]
    return {"title": f'{labels["trx_in"]} Summary', "label": labels["trx_in"], "data": data, "columns": columns}


# claude-sonnet-4-6
@ReportService.register("purchase_summary")
def _purchase_summary(db: Session, org_id: int, params: dict, columns: list):
    labels = resolve_labels(db, org_id)
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))
    status = params.get("status") or None

    q = (db.query(
            OutflowInvoice.number.label("invoice_no"),
            Party.name.label("vendor"),
            OutflowInvoice.doc_date.label("date"),
            OutflowInvoice.subtotal,
            OutflowInvoice.total_charge.label("tax"),
            OutflowInvoice.total_amount.label("total"),
            OutflowInvoice.status,
        )
        .join(Party, Party.id == OutflowInvoice.party_id)
        .filter(OutflowInvoice.org_id == org_id)
    )
    if date_from:
        q = q.filter(OutflowInvoice.doc_date >= date_from)
    if date_to:
        q = q.filter(OutflowInvoice.doc_date <= date_to)
    if status:
        q = q.filter(OutflowInvoice.status == status)
    q = q.order_by(OutflowInvoice.doc_date.desc()).limit(MAX_REPORT_ROWS)

    data = [row._asdict() for row in q.all()]
    return {"title": f'{labels["trx_out"]} Summary', "label": labels["trx_out"], "data": data, "columns": columns}


# claude-sonnet-4-6
@ReportService.register("trial_balance")
def _trial_balance_builtin(db: Session, org_id: int, params: dict, columns: list):
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))

    q = (db.query(
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            func.sum(JournalEntryLine.debit).label("total_debit"),
            func.sum(JournalEntryLine.credit).label("total_credit"),
        )
        .join(Account, Account.id == JournalEntryLine.account_id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(JournalEntry.status == "Posted", JournalEntry.org_id == org_id)
    )
    if date_from:
        q = q.filter(JournalEntry.doc_date >= date_from)
    if date_to:
        q = q.filter(JournalEntry.doc_date <= date_to)
    q = q.group_by(Account.code, Account.name).order_by(Account.code)

    data = [row._asdict() for row in q.all()]
    return {"title": "Trial Balance", "data": data, "columns": columns}


# claude-sonnet-4-6
@ReportService.register("profit_and_loss")
def _profit_and_loss(db: Session, org_id: int, params: dict, columns: list):
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))

    income_types = ("income_operating", "income_other")
    expense_types = ("expense_cogs", "expense_operating", "expense_other")

    q = (db.query(
            Account.account_type,
            Account.name.label("account_name"),
            (func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)).label("balance"),
        )
        .join(Account, Account.id == JournalEntryLine.account_id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(
            JournalEntry.status == "Posted",
            JournalEntry.org_id == org_id,
            Account.account_type.in_(income_types + expense_types),
        )
    )
    if date_from:
        q = q.filter(JournalEntry.doc_date >= date_from)
    if date_to:
        q = q.filter(JournalEntry.doc_date <= date_to)
    q = q.group_by(Account.id, Account.account_type, Account.name)

    rows = q.all()
    _CATEGORY = {
        "income_operating": "Revenue", "income_other": "Revenue",
        "expense_cogs": "Cost of Goods Sold",
        "expense_operating": "Operating Expenses",
        "expense_other": "Other Expenses",
    }
    _ORDER = {"Revenue": 1, "Cost of Goods Sold": 2, "Operating Expenses": 3, "Other Expenses": 4}
    data = sorted(
        [{"category": _CATEGORY[r.account_type], "account_name": r.account_name,
          "balance": r.balance if r.account_type in income_types else -r.balance}
         for r in rows],
        key=lambda x: _ORDER.get(x["category"], 5)
    )
    return {"title": "Profit & Loss", "data": data, "columns": columns}


# claude-sonnet-4-6
@ReportService.register("general_ledger")
def _general_ledger(db: Session, org_id: int, params: dict, columns: list):
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))

    q = (db.query(
            JournalEntry.doc_date.label("date"),
            JournalEntry.number.label("reference"),
            Account.name.label("account"),
            JournalEntryLine.debit,
            JournalEntryLine.credit,
            JournalEntryLine.description,
        )
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .join(Account, Account.id == JournalEntryLine.account_id)
        .filter(JournalEntry.status == "Posted", JournalEntry.org_id == org_id)
    )
    if date_from:
        q = q.filter(JournalEntry.doc_date >= date_from)
    if date_to:
        q = q.filter(JournalEntry.doc_date <= date_to)
    q = q.order_by(JournalEntry.doc_date.asc(), JournalEntry.id.asc()).limit(MAX_REPORT_ROWS)

    data = [row._asdict() for row in q.all()]
    return {"title": "General Ledger", "data": data, "columns": columns}


def _calc_outstanding(db, invoice_id: int, invoice_type: str, total: float) -> float:
    paid = (db.query(func.sum(PaymentAllocation.amount))
            .join(Payment, Payment.id == PaymentAllocation.payment_id)
            .filter(
                PaymentAllocation.invoice_id == invoice_id,
                PaymentAllocation.invoice_type == invoice_type,
                Payment.status == "Posted",
            ).scalar()) or 0.0
    return total - paid

# Import PaymentAllocation locally to avoid circulars if any, but it should be fine here.
from apps.accounting.models import PaymentAllocation

# claude-sonnet-4-6
@ReportService.register("ar_aging")
def _ar_aging(db: Session, org_id: int, params: dict, columns: list):
    today = date.today()

    rows = (db.query(InflowInvoice, Party.name.label("party_name"))
            .join(Party, Party.id == InflowInvoice.party_id)
            .filter(InflowInvoice.org_id == org_id,
                    InflowInvoice.status.in_(["Posted", "Partial"]))
            .all())

    data = []
    for inv, party_name in rows:
        outstanding = _calc_outstanding(db, inv.id, "InflowInvoice", inv.total_amount)
        if outstanding <= 0.01:
            continue
        days = (today - inv.doc_date).days if inv.doc_date else 0
        data.append({
            "party_name": party_name, "number": inv.number, "doc_date": inv.doc_date,
            "outstanding": outstanding, "days_outstanding": days,
            "0_30": outstanding if days <= 30 else 0,
            "31_60": outstanding if 31 <= days <= 60 else 0,
            "61_90": outstanding if 61 <= days <= 90 else 0,
            "over_90": outstanding if days > 90 else 0,
        })
    data.sort(key=lambda x: x["days_outstanding"], reverse=True)
    return {"title": "AR Aging", "data": data[:MAX_REPORT_ROWS], "columns": columns}


# claude-sonnet-4-6
@ReportService.register("ap_aging")
def _ap_aging(db: Session, org_id: int, params: dict, columns: list):
    today = date.today()

    rows = (db.query(OutflowInvoice, Party.name.label("party_name"))
            .join(Party, Party.id == OutflowInvoice.party_id)
            .filter(OutflowInvoice.org_id == org_id,
                    OutflowInvoice.status.in_(["Posted", "Partial"]))
            .all())

    data = []
    for inv, party_name in rows:
        outstanding = _calc_outstanding(db, inv.id, "OutflowInvoice", inv.total_amount)
        if outstanding <= 0.01:
            continue
        days = (today - inv.doc_date).days if inv.doc_date else 0
        data.append({
            "party_name": party_name, "number": inv.number, "doc_date": inv.doc_date,
            "outstanding": outstanding, "days_outstanding": days,
            "0_30": outstanding if days <= 30 else 0,
            "31_60": outstanding if 31 <= days <= 60 else 0,
            "61_90": outstanding if 61 <= days <= 90 else 0,
            "over_90": outstanding if days > 90 else 0,
        })
    data.sort(key=lambda x: x["days_outstanding"], reverse=True)
    return {"title": "AP Aging", "data": data[:MAX_REPORT_ROWS], "columns": columns}


# gpt-5
@ReportService.register("cash_flow")
def _cash_flow(db: Session, org_id: int, params: dict, columns: list):
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))
    if not date_from or not date_to:
        return {"title": "Cash Flow", "data": [], "columns": columns}

    inflows = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.org_id == org_id,
            Payment.status == "Posted",
            Payment.payment_type == "Incoming",
            Payment.doc_date >= date_from,
            Payment.doc_date <= date_to,
        )
        .scalar()
    ) or 0.0
    outflows = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.org_id == org_id,
            Payment.status == "Posted",
            Payment.payment_type == "Outgoing",
            Payment.doc_date >= date_from,
            Payment.doc_date <= date_to,
        )
        .scalar()
    ) or 0.0

    config = db.query(AccountingConfig).filter_by(org_id=org_id).first()
    cash_account_ids = {
        account_id
        for account_id in (
            getattr(config, "acc_cash_default_id", None),
            getattr(config, "acc_bank_default_id", None),
        )
        if account_id
    }
    if not cash_account_ids:
        fallback_rows = (
            db.query(Account.id)
            .filter(
                Account.org_id == org_id,
                Account.account_type == "asset_current",
                or_(Account.name.ilike("%cash%"), Account.name.ilike("%bank%"), Account.code.ilike("%111%")),
            )
            .all()
        )
        cash_account_ids = {row.id for row in fallback_rows}

    def _balance_as_of(as_of_date):
        if not cash_account_ids:
            return 0.0
        return (
            db.query(func.coalesce(func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0.0))
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
            .filter(
                JournalEntry.org_id == org_id,
                JournalEntry.status == "Posted",
                JournalEntryLine.account_id.in_(cash_account_ids),
                JournalEntry.doc_date <= as_of_date,
            )
            .scalar()
        ) or 0.0

    opening_anchor = date_from.fromordinal(date_from.toordinal() - 1)
    opening_balance = _balance_as_of(opening_anchor)
    closing_balance = _balance_as_of(date_to)
    net_cash_movement = inflows - outflows

    return {
        "title": "Cash Flow",
        "data": [
            {
                "opening_bank_balance": opening_balance,
                "cash_inflows": inflows,
                "cash_outflows": outflows,
                "net_cash_movement": net_cash_movement,
                "closing_bank_balance": closing_balance,
                "scope_note": "Best-effort summary from posted payments plus cash/bank GL balances.",
            }
        ],
        "columns": columns,
    }


# claude-sonnet-4-6
@ReportService.register("accounts_receivable")
def _accounts_receivable(db: Session, org_id: int, params: dict, columns: list):
    rows = (db.query(InflowInvoice, Party.name.label("customer"))
            .join(Party, Party.id == InflowInvoice.party_id)
            .filter(InflowInvoice.org_id == org_id, InflowInvoice.status == "Posted")
            .all())

    data = []
    for inv, customer in rows:
        balance = _calc_outstanding(db, inv.id, "InflowInvoice", inv.total_amount)
        if balance <= 0:
            continue
        data.append({
            "customer": customer, "invoice_no": inv.number,
            "date": inv.doc_date, "total_amount": inv.total_amount, "balance": balance,
        })
    return {"title": "Accounts Receivable Aging", "data": data, "columns": columns}


# gpt-5
@ReportService.register("tax_summary")
def _tax_summary(db: Session, org_id: int, params: dict, columns: list):
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))
    grouped: dict[tuple[str, str, int], dict] = {}

    def collect(invoice_model, line_model, direction: str):
        q = (
            db.query(line_model, invoice_model.doc_date, TaxRate)
            .join(invoice_model, invoice_model.id == line_model.invoice_id)
            .join(TaxRate, TaxRate.id == line_model.tax_rate_id)
            .filter(invoice_model.org_id == org_id, line_model.tax_amount > 0)
        )
        if date_from:
            q = q.filter(invoice_model.doc_date >= date_from)
        if date_to:
            q = q.filter(invoice_model.doc_date <= date_to)

        for line, doc_date, tax_rate in q.all():
            period = doc_date.strftime("%Y-%m") if doc_date else ""
            key = (period, direction, tax_rate.id)
            base_amount = float(line.amount) - float(line.tax_amount) if tax_rate.is_inclusive else float(line.amount)
            row = grouped.setdefault(key, {
                "period": period,
                "direction": direction,
                "tax_rate": tax_rate.name,
                "rate": float(tax_rate.rate),
                "taxable_base": 0.0,
                "tax_amount": 0.0,
            })
            row["taxable_base"] = round(row["taxable_base"] + base_amount, 10)
            row["tax_amount"] = round(row["tax_amount"] + float(line.tax_amount), 10)

    collect(InflowInvoice, InflowInvoiceLine, "Output Tax")
    collect(OutflowInvoice, OutflowInvoiceLine, "Input Tax")

    data = sorted(grouped.values(), key=lambda row: (row["period"], row["direction"], row["tax_rate"]))[:MAX_REPORT_ROWS]
    return {"title": "Tax Summary", "data": data, "columns": columns}


# ── Trade Dashboard Logic ───────────────────────────────────────────

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


# gemini-2.5-flash
def build_trade_dashboard(db: Session, org_id: int, current_user):
    today = date.today()
    month_start, month_end = _month_bounds(today)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start, _ = _month_bounds(prev_month_end)
    labels = resolve_labels(db, org_id)

    today_sales_rows = _sales_summary(
        db,
        org_id,
        {"date_from": today.isoformat(), "date_to": today.isoformat()},
        [],
    )["data"]
    month_profit_rows = _profit_and_loss(
        db,
        org_id,
        {"date_from": month_start.isoformat(), "date_to": month_end.isoformat()},
        [],
    )["data"]
    prev_month_profit_rows = _profit_and_loss(
        db,
        org_id,
        {"date_from": prev_month_start.isoformat(), "date_to": prev_month_end.isoformat()},
        [],
    )["data"]
    receivable_rows = _ar_aging(db, org_id, {}, [])["data"]
    
    # Stock summary is in another app. Call it through the registry to avoid importing apps.stock
    stock_summary_fn = ReportService._BUILTIN.get("stock_summary")
    if stock_summary_fn:
        stock_rows = stock_summary_fn(db, org_id, {}, [])["data"]
    else:
        stock_rows = []

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

    return {
        "labels": labels,
        "today_sales": today_sales,
        "month_profit": month_profit,
        "month_profit_change_pct": month_profit_change_pct,
        "receivables_total": sum(float(row.get("outstanding", 0) or 0) for row in receivable_rows),
        "overdue_count": sum(1 for row in receivable_rows if int(row.get("days_outstanding", 0) or 0) > 30),
        "low_stock_count": len(low_stock_items),
        "low_stock_items": low_stock_items[:5],
        "recent_documents": _recent_documents(db, org_id),
    }
