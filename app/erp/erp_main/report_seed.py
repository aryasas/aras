import json
from arasCore.lib.core.extensions import db
from app.erp.erp_main.models.report import ErpReport

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
  COALESCE(s.name, '') as vendor,
  pi.invoice_date as date,
  pi.subtotal,
  pi.charge_amt,
  pi.total,
  pi.state
FROM acc_purchase_invoice pi
LEFT JOIN sup_supplier s ON s.id = pi.supplier_id
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
from arasCore.lib.core.extensions import db
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
  (SELECT COUNT(*) FROM acc_sales_invoice si WHERE si.pos_session_id = ps.id) +
  (SELECT COUNT(*) FROM acc_purchase_invoice pi WHERE pi.pos_session_id = ps.id) as total_orders,
  COALESCE((SELECT SUM(si.total) FROM acc_sales_invoice si WHERE si.pos_session_id = ps.id), 0) -
  COALESCE((SELECT SUM(pi.total) FROM acc_purchase_invoice pi WHERE pi.pos_session_id = ps.id), 0) as net_sales,
  ps.opening_balance,
  ps.closing_balance,
  ps.cash_difference
FROM pos_session ps
JOIN auth_users u ON u.id = ps.cashier_id
JOIN pos_terminal pt ON pt.id = ps.terminal_id
WHERE pt.company_id = :company_id
  AND (:date_from IS NULL OR DATE(ps.opened_at) >= :date_from)
  AND (:date_to IS NULL OR DATE(ps.opened_at) <= :date_to)
ORDER BY ps.opened_at DESC""",
        "columns_json": json.dumps([
            {"field": "shift_number",     "label": "Shift No",       "type": "string"},
            {"field": "cashier",          "label": "Cashier",        "type": "string"},
            {"field": "terminal",         "label": "Terminal",       "type": "string"},
            {"field": "opened_at",        "label": "Opened",         "type": "datetime"},
            {"field": "closed_at",        "label": "Closed",         "type": "datetime"},
            {"field": "state",            "label": "State",          "type": "string"},
            {"field": "total_orders",     "label": "Orders",         "type": "integer"},
            {"field": "net_sales",        "label": "Net Sales",      "type": "currency"},
            {"field": "opening_balance",  "label": "Opening Bal.",   "type": "currency"},
            {"field": "closing_balance",  "label": "Closing Bal.",   "type": "currency"},
            {"field": "cash_difference",  "label": "Cash Diff.",     "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },
    {
        "name": "pot_sales_report",
        "title": "arasPos — Laporan Penjualan",
        "module": "pos",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  si.name                                 AS order_no,
  pt.name                                 AS terminal,
  ps.shift_number                         AS shift,
  COALESCE(cu.name, 'Walk-in')            AS customer,
  u.username                              AS cashier,
  si.invoice_date                         AS tanggal,
  si.subtotal,
  si.discount_amt,
  si.charge_amt                           AS tax_amt,
  si.total,
  si.state
FROM acc_sales_invoice si
JOIN pos_session ps   ON ps.id  = si.pos_session_id
JOIN pos_terminal pt  ON pt.id  = ps.terminal_id
JOIN auth_users u     ON u.id   = si.created_by_id
LEFT JOIN crm_customer cu ON cu.id = si.customer_id
WHERE si.company_id = :company_id
  AND si.state IN ('posted', 'paid')
  AND (:date_from IS NULL OR si.invoice_date >= :date_from)
  AND (:date_to   IS NULL OR si.invoice_date <= :date_to)
ORDER BY si.created_at DESC""",
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
        ]),
    },
    {
        "name": "pot_expense_report",
        "title": "arasPos — Laporan Pengeluaran",
        "module": "pos",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  pi.name                                 AS order_no,
  pt.name                                 AS terminal,
  ps.shift_number                         AS shift,
  u.username                              AS kasir,
  pi.invoice_date                         AS tanggal,
  pil.description                         AS item,
  pil.qty,
  pil.unit_price,
  pil.subtotal                            AS line_total
FROM acc_purchase_invoice pi
JOIN pos_session ps   ON ps.id  = pi.pos_session_id
JOIN pos_terminal pt  ON pt.id  = ps.terminal_id
JOIN auth_users u     ON u.id   = pi.created_by_id
JOIN acc_purchase_invoice_line pil ON pil.invoice_id = pi.id
WHERE pi.company_id = :company_id
  AND pi.state IN ('posted', 'paid')
  AND (:date_from IS NULL OR pi.invoice_date >= :date_from)
  AND (:date_to   IS NULL OR pi.invoice_date <= :date_to)
ORDER BY pi.created_at DESC""",
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
  p.code                                  AS kode,
  p.name                                  AS produk,
  SUM(sil.qty)                            AS total_qty,
  SUM(sil.subtotal)                       AS total_nilai,
  COUNT(DISTINCT si.id)                   AS jumlah_order
FROM acc_sales_invoice_line sil
JOIN acc_sales_invoice si ON si.id = sil.invoice_id
JOIN stock_product p ON p.id = sil.product_id
WHERE si.company_id = :company_id
  AND si.pos_session_id IS NOT NULL
  AND si.state IN ('posted', 'paid')
  AND (:date_from IS NULL OR si.invoice_date >= :date_from)
  AND (:date_to   IS NULL OR si.invoice_date <= :date_to)
GROUP BY p.id
ORDER BY total_nilai DESC""",
        "columns_json": json.dumps([
            {"field": "kode",         "label": "Kode",       "type": "string"},
            {"field": "produk",       "label": "Produk",     "type": "string"},
            {"field": "total_qty",    "label": "Total Qty",  "type": "number"},
            {"field": "total_nilai",  "label": "Total Nilai","type": "currency"},
            {"field": "jumlah_order", "label": "# Order",   "type": "integer"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Dari Tanggal", "type": "date"},
            {"field": "date_to",   "label": "S/d Tanggal",  "type": "date"},
        ]),
    },
    {
        "name": "trial_balance",
        "title": "Trial Balance",
        "module": "accounting",
        "report_type": "script",
        "render_mode": "custom",
        "script": """
from arasCore.lib.core.extensions import db
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
    WHERE a.account_type != 'view' AND a.is_group = 0
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
    {
        "name": "balance_sheet",
        "title": "Balance Sheet",
        "module": "accounting",
        "report_type": "query",
        "render_mode": "custom",
        "script": """SELECT code, name, amount FROM (
    SELECT 'ASSETS' as code, '' as name, 0.0 as amount, 1 as s1, 0 as s2
    UNION ALL SELECT '' as code, 'Current Assets' as name, 0.0 as amount, 2 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 2 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('asset_current', 'asset_cash') GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Fixed Assets' as name, 0.0 as amount, 3 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 3 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type = 'asset_fixed' GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Other Assets' as name, 0.0 as amount, 4 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 4 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type = 'asset_other' GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Total Assets' as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 9 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type LIKE 'asset_%'
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 10 as s1, 0 as s2
    UNION ALL SELECT 'LIABILITIES' as code, '' as name, 0.0 as amount, 11 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 12 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type LIKE 'liability_%' GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Total Liabilities' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 19 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type LIKE 'liability_%'
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 20 as s1, 0 as s2
    UNION ALL SELECT 'EQUITY' as code, '' as name, 0.0 as amount, 21 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 22 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type = 'equity' GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, '  Retained Earnings' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 23 as s1, 1 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other')
    UNION ALL SELECT '' as code, 'Total Equity' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 29 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE (a.account_type = 'equity' OR a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other'))
    UNION ALL SELECT '' as code, 'Total Liabilities + Equity' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 39 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE (a.account_type LIKE 'liability_%' OR a.account_type = 'equity' OR a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other'))
) t ORDER BY s1, s2, code""",
        "columns_json": json.dumps([
            {"field": "code",   "label": "Code",    "type": "string"},
            {"field": "name",   "label": "Account", "type": "string"},
            {"field": "amount", "label": "Amount",  "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_to", "label": "As of Date", "type": "date"},
        ]),
    },
    {
        "name": "cash_flow",
        "title": "Cash Flow Statement",
        "module": "accounting",
        "report_type": "query",
        "render_mode": "custom",
        "script": """SELECT code, name, amount FROM (
    SELECT 'OPERATING ACTIVITIES' as code, '' as name, 0.0 as amount, 1 as s1, 0 as s2
    UNION ALL SELECT '' as code, 'Inflows' as name, 0.0 as amount, 2 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 2 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('income_operating','income_other') AND a.is_group = 0 GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Outflows' as name, 0.0 as amount, 3 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 3 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('expense_operating','expense_cogs','expense_other') AND a.is_group = 0 GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Net Cash from Operations' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 9 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other')
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 10 as s1, 0 as s2
    UNION ALL SELECT 'INVESTING ACTIVITIES' as code, '' as name, 0.0 as amount, 11 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 12 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type = 'asset_fixed' AND a.is_group = 0 GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Net Cash from Investing' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 19 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type = 'asset_fixed'
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 20 as s1, 0 as s2
    UNION ALL SELECT 'FINANCING ACTIVITIES' as code, '' as name, 0.0 as amount, 21 as s1, 0 as s2
    UNION ALL SELECT a.code, CONCAT('  ', a.name) as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 22 as s1, 1 as s2
    FROM acc_account a LEFT JOIN acc_journal_line jl ON jl.account_id = a.id
    LEFT JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('equity','liability_long') AND a.is_group = 0 GROUP BY a.id HAVING amount != 0
    UNION ALL SELECT '' as code, 'Net Cash from Financing' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 29 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('equity','liability_long')
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 30 as s1, 0 as s2
    UNION ALL SELECT '' as code, 'NET CHANGE IN CASH' as name, COALESCE(SUM(jl.credit - jl.debit), 0) as amount, 31 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry >= :date_from) AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('income_operating','income_other','expense_operating','expense_cogs','expense_other','asset_fixed','equity','liability_long')
    UNION ALL SELECT '' as code, '' as name, 0.0 as amount, 40 as s1, 0 as s2
    UNION ALL SELECT '' as code, 'Cash at Beginning' as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 41 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_from IS NULL OR je.date_entry < :date_from)
    WHERE a.account_type IN ('asset_current', 'asset_cash')
    UNION ALL SELECT '' as code, 'Cash at End' as name, COALESCE(SUM(jl.debit - jl.credit), 0) as amount, 42 as s1, 0 as s2
    FROM acc_account a JOIN acc_journal_line jl ON jl.account_id = a.id
    JOIN acc_journal_entry je ON je.id = jl.entry_id AND je.company_id = :company_id AND je.state = 'posted' AND (:date_to IS NULL OR je.date_entry <= :date_to)
    WHERE a.account_type IN ('asset_current', 'asset_cash')
) t ORDER BY s1, s2, code""",
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
        "name": "general_ledger",
        "title": "General Ledger",
        "module": "accounting",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  je.date_entry as date,
  je.name as entry_no,
  a.code as account_code,
  a.name as account_name,
  jl.description,
  jl.debit,
  jl.credit
FROM acc_journal_line jl
JOIN acc_journal_entry je ON je.id = jl.entry_id
JOIN acc_account a ON a.id = jl.account_id
WHERE je.company_id = :company_id
  AND je.state = 'posted'
  AND (:date_from IS NULL OR je.date_entry >= :date_from)
  AND (:date_to IS NULL OR je.date_entry <= :date_to)
ORDER BY je.date_entry, je.id, jl.id""",
        "columns_json": json.dumps([
            {"field": "date",         "label": "Date",         "type": "date"},
            {"field": "entry_no",     "label": "Entry No",     "type": "string"},
            {"field": "account_code", "label": "Acc Code",     "type": "string"},
            {"field": "account_name", "label": "Account",      "type": "string"},
            {"field": "description",  "label": "Description",  "type": "string"},
            {"field": "debit",        "label": "Debit",        "type": "currency"},
            {"field": "credit",       "label": "Credit",       "type": "currency"},
        ]),
        "filters_json": json.dumps([
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ]),
    },
    {
        "name": "stock_summary",
        "title": "Stock Summary",
        "module": "stock",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  p.code,
  p.name,
  u.name as uom,
  COALESCE(SUM(CASE WHEN sm.dst_location_id IS NOT NULL THEN sml.qty_base ELSE 0 END) -
           SUM(CASE WHEN sm.src_location_id IS NOT NULL THEN sml.qty_base ELSE 0 END), 0) as balance
FROM stock_product p
JOIN stock_uom u ON u.id = p.uom_id
LEFT JOIN stock_movement_line sml ON sml.product_id = p.id
LEFT JOIN stock_movement sm ON sm.id = sml.movement_id AND sm.state = 'posted'
WHERE p.company_id = :company_id
GROUP BY p.id
HAVING balance != 0""",
        "columns_json": json.dumps([
            {"field": "code",    "label": "Code",    "type": "string"},
            {"field": "name",    "label": "Product", "type": "string"},
            {"field": "uom",     "label": "UoM",     "type": "string"},
            {"field": "balance", "label": "Balance", "type": "number"},
        ]),
        "filters_json": json.dumps([]),
    },
    {
        "name": "sales_by_product",
        "title": "Sales by Product",
        "module": "sales",
        "report_type": "query",
        "render_mode": "list",
        "script": """SELECT
  p.code,
  p.name,
  SUM(sil.qty) as total_qty,
  SUM(sil.subtotal) as total_amount
FROM acc_sales_invoice_line sil
JOIN acc_sales_invoice si ON si.id = sil.invoice_id
JOIN stock_product p ON p.id = sil.product_id
WHERE si.company_id = :company_id AND si.state IN ('posted', 'paid')
  AND (:date_from IS NULL OR si.invoice_date >= :date_from)
  AND (:date_to IS NULL OR si.invoice_date <= :date_to)
GROUP BY p.id
ORDER BY total_amount DESC""",
        "columns_json": json.dumps([
            {"field": "code",         "label": "Code",    "type": "string"},
            {"field": "name",         "label": "Product", "type": "string"},
            {"field": "total_qty",    "label": "Qty",     "type": "number"},
            {"field": "total_amount", "label": "Amount",  "type": "currency"},
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
            existing = ErpReport.find(name=r["name"])
            if not existing:
                ErpReport.create({**r, "is_active": True})
            else:
                existing.update_self({
                    "title": r.get("title", existing.title),
                    "script": r.get("script", existing.script),
                    "report_type": r.get("report_type", existing.report_type),
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
