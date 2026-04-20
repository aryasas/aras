import json
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.report import ErpReport

REPORTS = [
    {
        "name": "sales_summary",
        "title": "Sales Summary",
        "module": "accounting",
        "report_type": "query",
        "script": """SELECT
  si.name as invoice_no,
  cu.name as customer,
  si.invoice_date as date,
  si.subtotal,
  si.tax_amt,
  si.total,
  si.state
FROM acc_sales_invoice si
JOIN crm_customer cu ON cu.id = si.customer_id
WHERE si.company_id = :company_id
  AND (:date_from IS NULL OR si.invoice_date >= :date_from)
  AND (:date_to IS NULL OR si.invoice_date <= :date_to)
  AND (:state IS NULL OR si.state = :state)
ORDER BY si.invoice_date DESC""",
        "columns_json": json.dumps([
            {"field": "invoice_no", "label": "Invoice No", "type": "string"},
            {"field": "customer",   "label": "Customer",   "type": "string"},
            {"field": "date",       "label": "Date",       "type": "date"},
            {"field": "subtotal",   "label": "Subtotal",   "type": "currency"},
            {"field": "tax_amt",    "label": "Tax",        "type": "currency"},
            {"field": "total",      "label": "Total",      "type": "currency"},
            {"field": "state",      "label": "State",      "type": "string"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
            {"field": "state",     "label": "State",     "type": "select",
             "options": [("", "All"), ("draft", "Draft"), ("posted", "Posted"),
                         ("paid", "Paid"), ("cancelled", "Cancelled")]},
        ]),
    },
    {
        "name": "purchase_summary",
        "title": "Purchase Summary",
        "module": "accounting",
        "report_type": "query",
        "script": """SELECT
  pi.name as invoice_no,
  pi.vendor_name as vendor,
  pi.invoice_date as date,
  pi.subtotal,
  pi.tax_amt,
  pi.total,
  pi.state
FROM acc_purchase_invoice pi
WHERE pi.company_id = :company_id
  AND (:date_from IS NULL OR pi.invoice_date >= :date_from)
  AND (:date_to IS NULL OR pi.invoice_date <= :date_to)
  AND (:state IS NULL OR pi.state = :state)
ORDER BY pi.invoice_date DESC""",
        "columns_json": json.dumps([
            {"field": "invoice_no", "label": "Bill No",  "type": "string"},
            {"field": "vendor",     "label": "Vendor",   "type": "string"},
            {"field": "date",       "label": "Date",     "type": "date"},
            {"field": "subtotal",   "label": "Subtotal", "type": "currency"},
            {"field": "tax_amt",    "label": "Tax",      "type": "currency"},
            {"field": "total",      "label": "Total",    "type": "currency"},
            {"field": "state",      "label": "State",    "type": "string"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
            {"field": "state",     "label": "State",     "type": "select",
             "options": [("", "All"), ("draft", "Draft"), ("posted", "Posted"),
                         ("paid", "Paid"), ("cancelled", "Cancelled")]},
        ]),
    },
    {
        "name": "profit_and_loss",
        "title": "Profit & Loss",
        "module": "accounting",
        "report_type": "script",
        "script": """
from arasCore.lib.extensions import db
from decimal import Decimal

date_from = filters.get('date_from')
date_to   = filters.get('date_to')

def build_where(extra=""):
    conds = ["jl.entry_id = je.id", "je.company_id = :company_id", "je.state = 'posted'"]
    if date_from:
        conds.append("je.date_entry >= :date_from")
    if date_to:
        conds.append("je.date_entry <= :date_to")
    if extra:
        conds.append(extra)
    return " AND ".join(conds)

params = {"company_id": company_id, "date_from": date_from, "date_to": date_to}

revenue_sql = f'''
    SELECT a.code, a.name, SUM(jl.credit) - SUM(jl.debit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type IN ('income_operating','income_other')")}
    GROUP BY a.id ORDER BY a.code
'''
cogs_sql = f'''
    SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type = 'expense_cogs'")}
    GROUP BY a.id ORDER BY a.code
'''
opex_sql = f'''
    SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type = 'expense_operating'")}
    GROUP BY a.id ORDER BY a.code
'''

revenues = [(r[0], r[1], float(r[2] or 0)) for r in db.session.execute(db.text(revenue_sql), params)]
cogs     = [(r[0], r[1], float(r[2] or 0)) for r in db.session.execute(db.text(cogs_sql), params)]
opex     = [(r[0], r[1], float(r[2] or 0)) for r in db.session.execute(db.text(opex_sql), params)]

total_revenue = sum(r[2] for r in revenues)
total_cogs    = sum(r[2] for r in cogs)
total_opex    = sum(r[2] for r in opex)
gross_profit  = total_revenue - total_cogs
net_profit    = gross_profit - total_opex

rows = []
rows.append(["REVENUE", "", ""])
for code, name, amt in revenues:
    rows.append([code, name, amt])
rows.append(["", "Total Revenue", total_revenue])
rows.append(["", "", ""])
rows.append(["COGS", "", ""])
for code, name, amt in cogs:
    rows.append([code, name, amt])
rows.append(["", "Total COGS", total_cogs])
rows.append(["", "Gross Profit", gross_profit])
rows.append(["", "", ""])
rows.append(["OPERATING EXPENSES", "", ""])
for code, name, amt in opex:
    rows.append([code, name, amt])
rows.append(["", "Total OpEx", total_opex])
rows.append(["", "NET PROFIT", net_profit])

result["columns"] = [
    {"field": "code",   "label": "Code",   "type": "string"},
    {"field": "name",   "label": "Account","type": "string"},
    {"field": "amount", "label": "Amount", "type": "currency"},
]
result["data"] = rows
""",
        "columns_json": json.dumps([
            {"field": "code",   "label": "Code",    "type": "string"},
            {"field": "name",   "label": "Account", "type": "string"},
            {"field": "amount", "label": "Amount",  "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },
    {
        "name": "pos_shift_report",
        "title": "POS Shift Report",
        "module": "pos",
        "report_type": "query",
        "script": """SELECT
  ps.shift_number,
  u.username as cashier,
  pt.name as terminal,
  ps.opened_at,
  ps.closed_at,
  ps.state,
  COUNT(po.id) as total_orders,
  COALESCE(SUM(po.total), 0) as total_sales,
  ps.opening_balance,
  ps.closing_balance,
  ps.cash_difference
FROM pos_session ps
JOIN auth_users u ON u.id = ps.cashier_id
JOIN pos_terminal pt ON pt.id = ps.terminal_id
LEFT JOIN pos_order po ON po.session_id = ps.id AND po.state IN ('paid','invoiced')
WHERE pt.company_id = :company_id
  AND (:date_from IS NULL OR DATE(ps.opened_at) >= :date_from)
  AND (:date_to IS NULL OR DATE(ps.opened_at) <= :date_to)
GROUP BY ps.id
ORDER BY ps.opened_at DESC""",
        "columns_json": json.dumps([
            {"field": "shift_number",     "label": "Shift No",       "type": "string"},
            {"field": "cashier",          "label": "Cashier",        "type": "string"},
            {"field": "terminal",         "label": "Terminal",       "type": "string"},
            {"field": "opened_at",        "label": "Opened",         "type": "datetime"},
            {"field": "closed_at",        "label": "Closed",         "type": "datetime"},
            {"field": "state",            "label": "State",          "type": "string"},
            {"field": "total_orders",     "label": "Orders",         "type": "integer"},
            {"field": "total_sales",      "label": "Total Sales",    "type": "currency"},
            {"field": "opening_balance",  "label": "Opening Bal.",   "type": "currency"},
            {"field": "closing_balance",  "label": "Closing Bal.",   "type": "currency"},
            {"field": "cash_difference",  "label": "Cash Diff.",     "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },
]


def run_seed(app=None):
    def _do():
        for r in REPORTS:
            existing = ErpReport.query.filter_by(name=r["name"]).first()
            if not existing:
                db.session.add(ErpReport(**r))
        db.session.commit()
        print("[seed] report data seeded.")

    if app:
        with app.app_context():
            _do()
    else:
        _do()
