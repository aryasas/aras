import json
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.report import ErpReport

REPORTS = [
    {
        "name": "sales_summary",
        "title": "Sales Summary",
        "module": "accounting",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  si.name as invoice_no,
  cu.name as customer,
  si.invoice_date as date,
  si.subtotal,
  si.charge_amt,
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
            {"field": "date",       "label": "Date",     "type": "date"},
            {"field": "subtotal",   "label": "Subtotal", "type": "currency"},
            {"field": "charge_amt", "label": "Tax",      "type": "currency"},
            {"field": "total",      "label": "Total",    "type": "currency"},

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
        "render_mode": "list",
        "script": """SELECT
  pi.name as invoice_no,
  pi.vendor_name as vendor,
  pi.invoice_date as date,
  pi.subtotal,
  pi.charge_amt,
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
            {"field": "charge_amt", "label": "Tax",      "type": "currency"},
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
        "render_mode": "custom",
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
        "render_mode": "list",
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
REPORTS += [
    {
        "name": "pot_sales_report",
        "title": "arasPos — Laporan Penjualan",
        "module": "pos",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  po.name                                 AS order_no,
  pt.name                                 AS terminal,
  ps.shift_number                         AS shift,
  COALESCE(cu.name, 'Walk-in')            AS customer,
  u.username                              AS cashier,
  DATE(po.created_at)                     AS tanggal,
  po.subtotal,
  po.discount_amt,
  po.tax_amt,
  po.total,
  po.state
FROM pos_order po
JOIN pos_session ps   ON ps.id  = po.session_id
JOIN pos_terminal pt  ON pt.id  = ps.terminal_id
JOIN auth_users u     ON u.id   = po.cashier_id
LEFT JOIN crm_customer cu ON cu.id = po.customer_id
WHERE pt.company_id = :company_id
  AND pt.transaction_mode IN ('income','both')
  AND po.state IN ('paid','invoiced')
  AND (:date_from IS NULL OR DATE(po.created_at) >= :date_from)
  AND (:date_to   IS NULL OR DATE(po.created_at) <= :date_to)
  AND (:terminal_id IS NULL OR CAST(pt.id AS CHAR) = :terminal_id)
ORDER BY po.created_at DESC""",
        "columns_json": json.dumps([
            {"field": "order_no",     "label": "No Order",  "type": "string"},
            {"field": "terminal",     "label": "Terminal",  "type": "string"},
            {"field": "shift",        "label": "Shift",     "type": "string"},
            {"field": "customer",     "label": "Customer",  "type": "string"},
            {"field": "cashier",      "label": "Kasir",     "type": "string"},
            {"field": "tanggal",      "label": "Tanggal",   "type": "date"},
            {"field": "subtotal",     "label": "Subtotal",  "type": "currency"},
            {"field": "discount_amt", "label": "Diskon",    "type": "currency"},
            {"field": "tax_amt",      "label": "Pajak",     "type": "currency"},
            {"field": "total",        "label": "Total",     "type": "currency"},
            {"field": "state",        "label": "Status",    "type": "string"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from",   "label": "Dari Tanggal", "type": "date"},
            {"field": "date_to",     "label": "S/d Tanggal",  "type": "date"},
            {"field": "terminal_id", "label": "Terminal ID",  "type": "text"},
        ]),
    },
    {
        "name": "pot_expense_report",
        "title": "arasPos — Laporan Pengeluaran",
        "module": "pos",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  po.name                                 AS order_no,
  pt.name                                 AS terminal,
  ps.shift_number                         AS shift,
  u.username                              AS kasir,
  DATE(po.created_at)                     AS tanggal,
  pol.product_name                        AS item,
  pol.qty,
  pol.unit_price,
  pol.subtotal                            AS line_total
FROM pos_order po
JOIN pos_session ps   ON ps.id  = po.session_id
JOIN pos_terminal pt  ON pt.id  = ps.terminal_id
JOIN auth_users u     ON u.id   = po.cashier_id
JOIN pos_order_line pol ON pol.order_id = po.id
WHERE pt.company_id = :company_id
  AND pt.transaction_mode IN ('outcome','both')
  AND po.state IN ('paid','invoiced')
  AND (:date_from IS NULL OR DATE(po.created_at) >= :date_from)
  AND (:date_to   IS NULL OR DATE(po.created_at) <= :date_to)
ORDER BY po.created_at DESC, pol.id""",
        "columns_json": json.dumps([
            {"field": "order_no",   "label": "No Order",  "type": "string"},
            {"field": "terminal",   "label": "Terminal",  "type": "string"},
            {"field": "shift",      "label": "Shift",     "type": "string"},
            {"field": "kasir",      "label": "Kasir",     "type": "string"},
            {"field": "tanggal",    "label": "Tanggal",   "type": "date"},
            {"field": "item",       "label": "Item",      "type": "string"},
            {"field": "qty",        "label": "Qty",       "type": "number"},
            {"field": "unit_price", "label": "Harga",     "type": "currency"},
            {"field": "line_total", "label": "Total",     "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Dari Tanggal", "type": "date"},
            {"field": "date_to",   "label": "S/d Tanggal",  "type": "date"},
        ]),
    },
    {
        "name": "pot_summary_by_product",
        "title": "arasPos — Rekap Per Produk",
        "module": "pos",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  pol.product_code                        AS kode,
  pol.product_name                        AS produk,
  pt.transaction_mode                     AS mode,
  SUM(pol.qty)                            AS total_qty,
  SUM(pol.subtotal)                       AS total_nilai,
  COUNT(DISTINCT po.id)                   AS jumlah_order
FROM pos_order_line pol
JOIN pos_order po     ON po.id  = pol.order_id
JOIN pos_session ps   ON ps.id  = po.session_id
JOIN pos_terminal pt  ON pt.id  = ps.terminal_id
WHERE pt.company_id = :company_id
  AND po.state IN ('paid','invoiced')
  AND (:date_from IS NULL OR DATE(po.created_at) >= :date_from)
  AND (:date_to   IS NULL OR DATE(po.created_at) <= :date_to)
  AND (:tx_mode IS NULL OR pt.transaction_mode = :tx_mode)
GROUP BY pol.product_code, pol.product_name, pt.transaction_mode
ORDER BY total_nilai DESC""",
        "columns_json": json.dumps([
            {"field": "kode",         "label": "Kode",       "type": "string"},
            {"field": "produk",       "label": "Produk",     "type": "string"},
            {"field": "mode",         "label": "Mode",       "type": "string"},
            {"field": "total_qty",    "label": "Total Qty",  "type": "number"},
            {"field": "total_nilai",  "label": "Total Nilai","type": "currency"},
            {"field": "jumlah_order", "label": "# Order",   "type": "integer"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Dari Tanggal", "type": "date"},
            {"field": "date_to",   "label": "S/d Tanggal",  "type": "date"},
            {"field": "tx_mode",   "label": "Mode",         "type": "select",
             "options": [["", "Semua"], ["income", "Income"], ["outcome", "Outcome"]]},
        ]),
    },
]

REPORTS += [
    # ── Trial Balance ─────────────────────────────────────────────────────────
    {
        "name": "trial_balance",
        "title": "Trial Balance",
        "module": "accounting",
        "report_type": "script",
        "render_mode": "custom",
        "script": """
from arasCore.lib.extensions import db
from decimal import Decimal

date_from = filters.get('date_from')
date_to   = filters.get('date_to')

params = {"company_id": company_id, "date_from": date_from, "date_to": date_to}

sql = '''
    SELECT
        a.code,
        a.name,
        a.account_type,
        COALESCE(SUM(jl.debit),  0) AS total_debit,
        COALESCE(SUM(jl.credit), 0) AS total_credit,
        COALESCE(SUM(jl.debit),  0) - COALESCE(SUM(jl.credit), 0) AS balance
    FROM acc_account a
    LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id
        AND je.company_id = :company_id
        AND je.state = 'posted'
        AND (:date_from IS NULL OR je.date_entry >= :date_from)
        AND (:date_to   IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type != 'view'
    GROUP BY a.id
    ORDER BY a.code
'''

rows = []
total_dr = Decimal(0)
total_cr = Decimal(0)
for r in db.session.execute(db.text(sql), params):
    dr  = float(r[3])
    cr  = float(r[4])
    bal = float(r[5])
    total_dr += Decimal(str(dr))
    total_cr += Decimal(str(cr))
    rows.append([r[0], r[1], r[2], dr, cr, bal])

rows.append(["", "TOTAL", "", float(total_dr), float(total_cr),
             float(total_dr) - float(total_cr)])

result["columns"] = [
    {"field": "code",    "label": "Code",         "type": "string"},
    {"field": "name",    "label": "Account",      "type": "string"},
    {"field": "type",    "label": "Type",         "type": "string"},
    {"field": "debit",   "label": "Debit",        "type": "currency"},
    {"field": "credit",  "label": "Credit",       "type": "currency"},
    {"field": "balance", "label": "Balance",      "type": "currency"},
]
result["data"] = rows
""",
        "columns_json": json.dumps([
            {"field": "code",    "label": "Code",    "type": "string"},
            {"field": "name",    "label": "Account", "type": "string"},
            {"field": "type",    "label": "Type",    "type": "string"},
            {"field": "debit",   "label": "Debit",   "type": "currency"},
            {"field": "credit",  "label": "Credit",  "type": "currency"},
            {"field": "balance", "label": "Balance", "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },

    # ── Cash Flow Statement ───────────────────────────────────────────────────
    {
        "name": "cash_flow",
        "title": "Cash Flow Statement",
        "module": "accounting",
        "report_type": "script",
        "render_mode": "custom",
        "script": """
from arasCore.lib.extensions import db
from decimal import Decimal

date_from = filters.get('date_from')
date_to   = filters.get('date_to')
params = {"company_id": company_id, "date_from": date_from, "date_to": date_to}

def build_where(extra=""):
    conds = ["jl.entry_id = je.id", "je.company_id = :company_id", "je.state = 'posted'"]
    if date_from:
        conds.append("je.date_entry >= :date_from")
    if date_to:
        conds.append("je.date_entry <= :date_to")
    if extra:
        conds.append(extra)
    return " AND ".join(conds)

# Operating: revenue accounts (credit = inflow) + expense accounts (debit = outflow)
revenue_sql = f'''SELECT a.code, a.name, SUM(jl.credit) - SUM(jl.debit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type IN ('income_operating','income_other')")}
    GROUP BY a.id ORDER BY a.code'''

expense_sql = f'''SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type IN ('expense_operating','expense_cogs','expense_other')")}
    GROUP BY a.id ORDER BY a.code'''

# Investing: fixed asset accounts
invest_sql = f'''SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type = 'asset_fixed'")}
    GROUP BY a.id ORDER BY a.code'''

# Financing: equity + long-term liability
finance_sql = f'''SELECT a.code, a.name, SUM(jl.credit) - SUM(jl.debit) as amount
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE {build_where("a.account_type IN ('equity','liability_long')")}
    GROUP BY a.id ORDER BY a.code'''

def run(sql):
    return [(r[0], r[1], float(r[2] or 0)) for r in db.session.execute(db.text(sql), params)]

revenues   = run(revenue_sql)
expenses   = run(expense_sql)
investing  = run(invest_sql)
financing  = run(finance_sql)

op_inflow  = sum(r[2] for r in revenues)
op_outflow = sum(r[2] for r in expenses)
net_op     = op_inflow - op_outflow
net_inv    = -sum(r[2] for r in investing)   # net outflow for capex
net_fin    = sum(r[2] for r in financing)
net_change = net_op + net_inv + net_fin

rows = []
rows.append(["OPERATING ACTIVITIES", "", ""])
rows.append(["", "Cash receipts from customers", op_inflow])
for code, name, amt in revenues:
    rows.append([code, f"  {name}", amt])
rows.append(["", "Cash paid for expenses", -op_outflow])
for code, name, amt in expenses:
    rows.append([code, f"  {name}", -amt])
rows.append(["", "Net Cash from Operations", net_op])
rows.append(["", "", ""])

rows.append(["INVESTING ACTIVITIES", "", ""])
for code, name, amt in investing:
    rows.append([code, name, -amt])
rows.append(["", "Net Cash from Investing", net_inv])
rows.append(["", "", ""])

rows.append(["FINANCING ACTIVITIES", "", ""])
for code, name, amt in financing:
    rows.append([code, name, amt])
rows.append(["", "Net Cash from Financing", net_fin])
rows.append(["", "", ""])

rows.append(["", "NET CHANGE IN CASH", net_change])

result["columns"] = [
    {"field": "code",   "label": "Code",    "type": "string"},
    {"field": "name",   "label": "Item",    "type": "string"},
    {"field": "amount", "label": "Amount",  "type": "currency"},
]
result["data"] = rows
""",
        "columns_json": json.dumps([
            {"field": "code",   "label": "Code",   "type": "string"},
            {"field": "name",   "label": "Item",   "type": "string"},
            {"field": "amount", "label": "Amount", "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },

    # ── Balance Sheet ─────────────────────────────────────────────────────────
    {
        "name": "balance_sheet",
        "title": "Balance Sheet",
        "module": "accounting",
        "report_type": "script",
        "render_mode": "custom",
        "script": """
from arasCore.lib.extensions import db
from decimal import Decimal

as_of = filters.get('date_to')
params = {"company_id": company_id, "date_to": as_of}

def build_where(type_filter):
    conds = ["jl.entry_id = je.id", "je.company_id = :company_id", "je.state = 'posted'", type_filter]
    if as_of:
        conds.append("je.date_entry <= :date_to")
    return " AND ".join(conds)

def run(type_filter, side):
    sql = f'''SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as balance
        FROM acc_journal_line jl
        JOIN acc_journal_entry je ON je.id = jl.entry_id
        JOIN acc_account a ON a.id = jl.account_id
        WHERE {build_where(type_filter)}
        GROUP BY a.id ORDER BY a.code'''
    rows = db.session.execute(db.text(sql), params)
    results = [(r[0], r[1], float(r[2] or 0)) for r in rows]
    if side == 'credit':
        results = [(c, n, -v) for c, n, v in results]
    return results

assets_curr  = run("a.account_type = 'asset_current'",  'debit')
assets_fixed = run("a.account_type = 'asset_fixed'",    'debit')
assets_other = run("a.account_type = 'asset_other'",    'debit')
liab_curr    = run("a.account_type = 'liability_current'", 'credit')
liab_long    = run("a.account_type = 'liability_long'",    'credit')
equity       = run("a.account_type = 'equity'",            'credit')

# Retained earnings: net income to date
ret_sql = '''SELECT COALESCE(SUM(CASE WHEN a.account_type IN ('income_operating','income_other')
                    THEN jl.credit - jl.debit ELSE jl.debit - jl.credit END), 0)
    FROM acc_journal_line jl
    JOIN acc_journal_entry je ON je.id = jl.entry_id
    JOIN acc_account a ON a.id = jl.account_id
    WHERE je.company_id = :company_id AND je.state = 'posted'
    AND a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other')
''' + ("AND je.date_entry <= :date_to" if as_of else "")
retained = float(db.session.execute(db.text(ret_sql), params).scalar() or 0)

total_assets = sum(v for _,_,v in assets_curr+assets_fixed+assets_other)
total_liab   = sum(v for _,_,v in liab_curr+liab_long)
total_equity = sum(v for _,_,v in equity) + retained
total_le     = total_liab + total_equity

rows = []
rows.append(["ASSETS", "", ""])
rows.append(["", "Current Assets", ""])
for c, n, v in assets_curr:
    rows.append([c, f"  {n}", v])
rows.append(["", "Fixed Assets", ""])
for c, n, v in assets_fixed:
    rows.append([c, f"  {n}", v])
for c, n, v in assets_other:
    rows.append([c, f"  {n}", v])
rows.append(["", "Total Assets", total_assets])
rows.append(["", "", ""])

rows.append(["LIABILITIES", "", ""])
for c, n, v in liab_curr + liab_long:
    rows.append([c, f"  {n}", v])
rows.append(["", "Total Liabilities", total_liab])
rows.append(["", "", ""])

rows.append(["EQUITY", "", ""])
for c, n, v in equity:
    rows.append([c, f"  {n}", v])
rows.append(["", "  Retained Earnings", retained])
rows.append(["", "Total Equity", total_equity])
rows.append(["", "", ""])
rows.append(["", "Total Liabilities + Equity", total_le])

result["columns"] = [
    {"field": "code",   "label": "Code",    "type": "string"},
    {"field": "name",   "label": "Account", "type": "string"},
    {"field": "amount", "label": "Amount",  "type": "currency"},
]
result["data"] = rows
""",
        "columns_json": json.dumps([
            {"field": "code",   "label": "Code",    "type": "string"},
            {"field": "name",   "label": "Account", "type": "string"},
            {"field": "amount", "label": "Amount",  "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_to", "label": "As of Date", "type": "date"},
        ]),
    },
]



def run_seed(app=None):
    def _do():
        for r in REPORTS:
            existing = ErpReport.find(name=r["name"])
            if not existing:
                ErpReport.create({**r, "is_active": True})
            else:
                existing.update_self({
                    "title": r.get("title", existing.title),
                    "script": r.get("script", existing.script),
                    "render_mode": r.get("render_mode", "list"),
                    "columns_json": r.get("columns_json", existing.columns_json),
                    "filters_json": r.get("filters_json", existing.filters_json),
                    "is_active": True,
                })
        print("[seed] report data seeded.")

    if app:
        with app.app_context():
            _do()
    else:
        _do()
