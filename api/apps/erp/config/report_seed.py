from sqlalchemy.orm import Session
from core import Aras # Import Aras to access registry

REPORTS = [
    {
        "code": "sales_summary",
        "name": "Sales Summary",
        "module": "accounting",
        "report_type": "query",
        "linked_doctype": "SalesInvoice",
        "script": """SELECT
  si.name as invoice_no,
  cu.name as customer,
  si.doc_date as date,
  si.subtotal,
  si.total_charge as tax,
  si.total_amount as total,
  si.status
FROM erp_accounting_sales_invoices si
JOIN erp_crm_customers cu ON cu.id = si.customer_id
WHERE si.company_id = :company_id
  AND (:date_from IS NULL OR si.doc_date >= :date_from)
  AND (:date_to IS NULL OR si.doc_date <= :date_to)
  AND (:status IS NULL OR si.status = :status)
ORDER BY si.doc_date DESC""",
        "columns_json": [
            {"field": "invoice_no", "label": "Invoice No", "type": "string"},
            {"field": "customer",   "label": "Customer",   "type": "string"},
            {"field": "date",       "label": "Date",     "type": "date"},
            {"field": "subtotal",   "label": "Subtotal", "type": "currency"},
            {"field": "tax",        "label": "Tax",      "type": "currency"},
            {"field": "total",      "label": "Total",    "type": "currency"},
            {"field": "status",     "label": "Status",    "type": "string"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
            {"field": "status",     "label": "Status",     "type": "select",
             "options": [("", "All"), ("Draft", "Draft"), ("Posted", "Posted"),
                         ("Paid", "Paid"), ("Cancelled", "Cancelled")]},
        ],
    },
    {
        "code": "purchase_summary",
        "name": "Purchase Summary",
        "module": "accounting",
        "report_type": "query",
        "linked_doctype": "PurchaseInvoice",
        "script": """SELECT
  pi.name as invoice_no,
  s.name as vendor,
  pi.doc_date as date,
  pi.subtotal,
  pi.total_charge as tax,
  pi.total_amount as total,
  pi.status
FROM erp_accounting_purchase_invoices pi
JOIN erp_supplier_suppliers s ON s.id = pi.supplier_id
WHERE pi.company_id = :company_id
  AND (:date_from IS NULL OR pi.doc_date >= :date_from)
  AND (:date_to IS NULL OR pi.doc_date <= :date_to)
  AND (:status IS NULL OR pi.status = :status)
ORDER BY pi.doc_date DESC""",
        "columns_json": [
            {"field": "invoice_no", "label": "Bill No",  "type": "string"},
            {"field": "vendor",     "label": "Vendor",   "type": "string"},
            {"field": "date",       "label": "Date",     "type": "date"},
            {"field": "subtotal",   "label": "Subtotal", "type": "currency"},
            {"field": "tax",        "label": "Tax",      "type": "currency"},
            {"field": "total",      "label": "Total",    "type": "currency"},
            {"field": "status",     "label": "Status",    "type": "string"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
            {"field": "status",     "label": "Status",     "type": "select",
             "options": [("", "All"), ("Draft", "Draft"), ("Posted", "Posted"),
                         ("Paid", "Paid"), ("Cancelled", "Cancelled")]},
        ],
    },
    {
        "code": "profit_and_loss",
        "name": "Profit & Loss",
        "module": "accounting",
        "report_type": "script",
        "script": """
from core.lib.db import db
from decimal import Decimal

date_from = filters.get('date_from')
date_to   = filters.get('date_to')

def build_where(extra=""):
    conds = ["jl.entry_id = je.id", "je.company_id = :company_id", "je.status = 'Posted'"]
    if date_from:
        conds.append("je.doc_date >= :date_from")
    if date_to:
        conds.append("je.doc_date <= :date_to")
    if extra:
        conds.append(extra)
    return " AND ".join(conds)

params = {"company_id": company_id, "date_from": date_from, "date_to": date_to}

revenue_sql = f'''
    SELECT a.code, a.name, SUM(jl.credit) - SUM(jl.debit) as amount
    FROM erp_accounting_entry_lines jl
    JOIN erp_accounting_entries je ON je.id = jl.entry_id
    JOIN erp_accounting_accounts a ON a.id = jl.account_id
    WHERE {build_where("a.account_type IN ('income_operating','income_other')")}
    GROUP BY a.id ORDER BY a.code
'''
cogs_sql = f'''
    SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM erp_accounting_entry_lines jl
    JOIN erp_accounting_entries je ON je.id = jl.entry_id
    JOIN erp_accounting_accounts a ON a.id = jl.account_id
    WHERE {build_where("a.account_type = 'expense_cogs'")}
    GROUP BY a.id ORDER BY a.code
'''
opex_sql = f'''
    SELECT a.code, a.name, SUM(jl.debit) - SUM(jl.credit) as amount
    FROM erp_accounting_entry_lines jl
    JOIN erp_accounting_entries je ON je.id = jl.entry_id
    JOIN erp_accounting_accounts a ON a.id = jl.account_id
    WHERE {build_where("a.account_type = 'expense_operating'")}
    GROUP BY a.id ORDER BY a.code
'''

session = db()
revenues = [(r[0], r[1], float(r[2] or 0)) for r in session.execute(db.text(revenue_sql), params)]
cogs     = [(r[0], r[1], float(r[2] or 0)) for r in session.execute(db.text(cogs_sql), params)]
opex     = [(r[0], r[1], float(r[2] or 0)) for r in session.execute(db.text(opex_sql), params)]

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
        "columns_json": [
            {"field": "code",   "label": "Code",    "type": "string"},
            {"field": "name",   "label": "Account", "type": "string"},
            {"field": "amount", "label": "Amount",  "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ],
    },
    {
        "code": "trial_balance",
        "name": "Trial Balance",
        "module": "accounting",
        "report_type": "script",
        "script": """
from core.lib.db import db
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
    FROM erp_accounting_accounts a
    LEFT JOIN erp_accounting_entry_lines jl ON jl.account_id = a.id
    LEFT JOIN erp_accounting_entries je ON je.id = jl.entry_id
        AND je.company_id = :company_id
        AND je.status = 'Posted'
        AND (:date_from IS NULL OR je.doc_date >= :date_from)
        AND (:date_to   IS NULL OR je.doc_date <= :date_to)
    WHERE a.account_type != 'view' AND a.is_group = 0
    GROUP BY a.id
    ORDER BY a.code
'''

session = db()
rows = []
total_dr = Decimal(0)
total_cr = Decimal(0)
for r in session.execute(db.text(sql), params):
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
        "columns_json": [
            {"field": "code",    "label": "Code",    "type": "string"},
            {"field": "name",    "label": "Account", "type": "string"},
            {"field": "type",    "label": "Type",    "type": "string"},
            {"field": "debit",   "label": "Debit",   "type": "currency"},
            {"field": "credit",  "label": "Credit",  "type": "currency"},
            {"field": "balance", "label": "Balance", "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ],
    },
    {
        "code": "stock_summary",
        "name": "Stock Summary",
        "module": "stock",
        "report_type": "query",
        "script": """SELECT
  p.code,
  p.name,
  u.name as uom,
  COALESCE(SUM(CASE WHEN sm.to_location_id IS NOT NULL THEN sml.qty ELSE 0 END) -
           SUM(CASE WHEN sm.from_location_id IS NOT NULL THEN sml.qty ELSE 0 END), 0) as balance
FROM erp_stock_products p
JOIN erp_config_uoms u ON u.id = p.uom_id
LEFT JOIN erp_stock_movement_lines sml ON sml.product_id = p.id
LEFT JOIN erp_stock_movements sm ON sm.id = sml.movement_id AND sm.status = 'Posted'
WHERE p.company_id = :company_id
GROUP BY p.id
HAVING balance != 0""",
        "columns_json": [
            {"field": "code",    "label": "Code",    "type": "string"},
            {"field": "name",    "label": "Product", "type": "string"},
            {"field": "uom",     "label": "UoM",     "type": "string"},
            {"field": "balance", "label": "Balance", "type": "number"},
        ],
        "filters_json": [],
    },
]


def run_seed(db: Session, company_id: int):
    Report = Aras.Model._registry["Report"] 
    for r in REPORTS:
        existing = Report.find(db, code=r["code"], company_id=company_id)
        if not existing:
            Report.create(db, {**r, "company_id": company_id})
        else:
            existing.update_self(db, {
                "name": r["name"],
                "script": r["script"],
                "report_type": r["report_type"],
                "columns_json": r["columns_json"],
                "filters_json": r["filters_json"],
            })
    print(f"[seed] report data seeded for company {company_id}.")
