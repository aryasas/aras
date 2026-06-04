# gemini-flash
import logging
import concurrent.futures
from datetime import date, datetime, timezone
from core import Aras
from core.lib.query_builder import QueryBuilder
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from apps.accounting.services.vocabulary import resolve_labels

logger = logging.getLogger(__name__)

MAX_REPORT_ROWS = 1000


class ReportService(Aras.Service):
    _BUILTIN: dict = {}

    @classmethod
    def register(cls, code: str):
        """Decorator to register a builtin report function by code."""
        def decorator(fn):
            cls._BUILTIN[code] = fn
            return fn
        return decorator

    @classmethod
    def generate(cls, report_instance, filters=None, db=None, current_user=None):
        """Execute a database-defined builtin or ORM report."""
        db = db or report_instance.db_session
        if not db:
            return {"error": "Database session not found for report instance."}

        params = {"org_id": report_instance.org_id}
        filter_defs = report_instance.filters_json or []
        if isinstance(filter_defs, list):
            for fdef in filter_defs:
                field = fdef.get("field")
                if field:
                    params[field] = fdef.get("default")
        elif isinstance(filter_defs, dict):
            params.update(filter_defs)
        if filters:
            params.update({k: v for k, v in filters.items() if v not in (None, "", "None")})

        if report_instance.report_type == "builtin":
            fn = cls._BUILTIN.get(report_instance.code)
            if not fn:
                return {"error": f"Builtin report '{report_instance.code}' not registered.", "data": [], "columns": []}
            try:
                result = fn(db=db, org_id=report_instance.org_id, params=params,
                            columns=report_instance.columns_json or [])
                result["filters_json"] = filter_defs
                return result
            except Exception as e:
                logger.exception(f"builtin report failed: {report_instance.code}")
                return {"error": str(e), "data": [], "columns": [], "filters_json": filter_defs}

        if report_instance.report_type == "orm":
            result = cls._generate_orm_report(report_instance, db, params)
        elif report_instance.report_type == "script":
            result = cls._generate_script_report(report_instance, db, params, current_user)
        else:
            return {"error": f"Report type '{report_instance.report_type}' not supported.", "data": [], "columns": []}

        result["filters_json"] = filter_defs
        return result

    @classmethod
    def _generate_script_report(cls, report, db, params, current_user):
        """Execute a Python script report with hardening."""
        # Gate behind superuser (is_admin in this framework)
        if not current_user or not getattr(current_user, "is_admin", False):
            return {"error": "403 Forbidden: Script reports require administrator privileges."}

        # Approval check
        if not report.script_approved_by_id:
            return {"error": "Report script is not approved for execution."}

        if not report.script:
            return {"error": "No script defined for this report."}

        # Whitelist globals
        safe_globals = {
            "db": db,
            "params": params,
            "result": None,
            "datetime": datetime,
            "date": date,
            "__builtins__": {} # NO __builtins__
        }

        start_time = datetime.now(timezone.utc)
        try:
            # Wrap in executor for timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(exec, report.script, safe_globals)
                future.result(timeout=5) # 5s timeout
            
            result_data = safe_globals.get("result")
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log execution
            logger.info(f"Script report execution: user_id={current_user.id}, report_id={report.id}, duration={duration}s")
            
            if result_data is None:
                return {"error": "Script executed but 'result' variable was not set.", "data": [], "columns": report.columns_json or []}
            
            return {
                "title": report.name,
                "data": result_data if isinstance(result_data, list) else [],
                "columns": report.columns_json or []
            }
        except concurrent.futures.TimeoutError:
            logger.error(f"Script report timeout: user_id={getattr(current_user, 'id', 'unknown')}, report_id={report.id}")
            return {"error": "Script execution timed out after 5 seconds."}
        except Exception as e:
            logger.exception(f"Script report failed: {report.id}")
            return {"error": f"Script execution error: {str(e)}"}

    @classmethod
    def _generate_orm_report(cls, report, db, params):
        """Execute via ORM + QueryBuilder — no raw SQL."""
        if not report.linked_doctype:
            return {"error": "ORM report requires linked_doctype.", "data": [], "columns": []}

        model_class = Aras.Model._registry.get(report.linked_doctype)
        if not model_class:
            return {"error": f"Model {report.linked_doctype} not found.", "data": [], "columns": []}

        try:
            qb_filters = list(report.query_filters or [])
            if not any(f.get("field") == "org_id" for f in qb_filters):
                qb_filters.insert(0, {"field": "org_id", "op": "==", "value": report.org_id})

            runtime_filters = [
                {"field": k, "op": "==", "value": v}
                for k, v in filters.items()
                if v not in (None, "", "None") and k not in ("org_id",)
            ]
            results = QueryBuilder.execute(db, model_class, qb_filters + runtime_filters)
            columns = report.columns_json or [
                {"field": c.name, "label": c.name} for c in model_class.__table__.columns
            ]
            data = []
            for item in results[:MAX_REPORT_ROWS]:
                row = {col["field"]: getattr(item, col["field"], None) for col in columns if "field" in col}
                data.append(row)

            return {"title": report.name, "data": data, "columns": columns}
        except Exception as e:
            logger.exception("orm report failed")
            return {"error": str(e), "data": [], "columns": []}


# ── Builtin Report Implementations ───────────────────────────────────────────

def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except ValueError:
        return None


# claude-sonnet-4-6
@ReportService.register("sales_summary")
def _sales_summary(db: Session, org_id: int, params: dict, columns: list):
    from apps.accounting.models import InflowInvoice
    from apps.party.models import Party
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
    from apps.accounting.models import OutflowInvoice
    from apps.party.models import Party
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
def _trial_balance(db: Session, org_id: int, params: dict, columns: list):
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account
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
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account
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
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account
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
    from apps.accounting.models import PaymentAllocation, Payment
    paid = (db.query(func.sum(PaymentAllocation.amount))
            .join(Payment, Payment.id == PaymentAllocation.payment_id)
            .filter(
                PaymentAllocation.invoice_id == invoice_id,
                PaymentAllocation.invoice_type == invoice_type,
                Payment.status == "Posted",
            ).scalar()) or 0.0
    return total - paid


# claude-sonnet-4-6
@ReportService.register("ar_aging")
def _ar_aging(db: Session, org_id: int, params: dict, columns: list):
    from apps.accounting.models import InflowInvoice
    from apps.party.models import Party
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
    from apps.accounting.models import OutflowInvoice
    from apps.party.models import Party
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


# claude-sonnet-4-6
@ReportService.register("stock_summary")
def _stock_summary(db: Session, org_id: int, params: dict, columns: list):
    from apps.stock.models import Item, StockMovement, StockMovementLine
    from plugins.commerce.models import Uom

    inbound_location = func.coalesce(StockMovementLine.to_location_id, StockMovement.to_location_id)
    outbound_location = func.coalesce(StockMovementLine.from_location_id, StockMovement.from_location_id)
    balance_expr = func.coalesce(
        func.sum(case((inbound_location.isnot(None), StockMovementLine.qty), else_=0)) -
        func.sum(case((outbound_location.isnot(None), StockMovementLine.qty), else_=0)),
        0
    )

    q = (db.query(
            Item.code.label("code"),
            Item.name.label("name"),
            func.coalesce(Uom.name, "").label("uom"),
            balance_expr.label("balance"),
        )
        .join(StockMovementLine, StockMovementLine.item_id == Item.id)
        .join(StockMovement, StockMovement.id == StockMovementLine.movement_id)
        .outerjoin(Uom, Uom.id == Item.uom_id)
        .filter(
            StockMovement.org_id == org_id,
            StockMovement.status == "Posted",
            StockMovement.deleted_at.is_(None),
            StockMovementLine.deleted_at.is_(None),
        )
        .group_by(Item.id, Item.code, Item.name, Uom.name)
        .having(balance_expr != 0)
        .order_by(Item.code, Item.name)
    )
    data = [row._asdict() for row in q.all()]
    return {"title": "Stock Summary", "data": data, "columns": columns}


# claude-sonnet-4-6
@ReportService.register("accounts_receivable")
def _accounts_receivable(db: Session, org_id: int, params: dict, columns: list):
    from apps.accounting.models import InflowInvoice
    from apps.party.models import Party

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
