from sqlalchemy.orm import Session
from core import Aras # Import Aras to access registry

REPORTS = [
    {
        "code": "sales_summary",
        "name": "Sales Summary",
        "module": "accounting",
        "report_type": "query",
        "linked_doctype": "InflowInvoice",
        "script": """SELECT
  si.number as invoice_no,
  cu.name as customer,
  si.doc_date as date,
  si.subtotal,
  si.total_charge as tax,
  si.total_amount as total,
  si.status
FROM erp_accounting_inflow_invoices si
JOIN erp_party_parties cu ON cu.id = si.party_id
WHERE si.org_id = :org_id
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
        "linked_doctype": "OutflowInvoice",
        "script": """SELECT
  pi.number as invoice_no,
  s.name as vendor,
  pi.doc_date as date,
  pi.subtotal,
  pi.total_charge as tax,
  pi.total_amount as total,
  pi.status
FROM erp_accounting_outflow_invoices pi
JOIN erp_party_parties s ON s.id = pi.party_id
WHERE pi.org_id = :org_id
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
        "code": "trial_balance",
        "name": "Trial Balance",
        "module": "accounting",
        "report_type": "query",
        "script": """
    SELECT
        a.code as account_code,
        a.name as account_name,
        SUM(jl.debit) as total_debit,
        SUM(jl.credit) as total_credit
    FROM erp_accounting_journal_lines jl
    JOIN erp_accounting_accounts a ON a.id = jl.account_id
    JOIN erp_accounting_entries je ON je.id = jl.entry_id
    WHERE je.status = 'Posted' AND je.org_id = :org_id
        AND (:date_from IS NULL OR je.doc_date >= :date_from)
        AND (:date_to IS NULL OR je.doc_date <= :date_to)
    GROUP BY a.code, a.name
    ORDER BY a.code
    """,
        "columns_json": [
            {"field": "account_code", "label": "Account Code", "type": "string"},
            {"field": "account_name", "label": "Account Name", "type": "string"},
            {"field": "total_debit", "label": "Debit", "type": "currency"},
            {"field": "total_credit", "label": "Credit", "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ],
    },
    {
        "code": "profit_and_loss",
        "name": "Profit & Loss",
        "module": "accounting",
        "report_type": "query",
        "script": """
    WITH monthly_balances AS (
        SELECT
            a.account_type,
            a.name AS account_name,
            SUM(jl.credit) - SUM(jl.debit) AS balance
        FROM erp_accounting_journal_lines jl
        JOIN erp_accounting_accounts a ON jl.account_id = a.id
        JOIN erp_accounting_entries je ON jl.entry_id = je.id
        WHERE
            je.status = 'Posted'
            AND je.org_id = :org_id
            AND a.account_type IN ('income_operating', 'income_other', 'expense_cogs', 'expense_operating', 'expense_other')
            AND (:date_from IS NULL OR je.doc_date >= :date_from)
            AND (:date_to IS NULL OR je.doc_date <= :date_to)
        GROUP BY a.id
    )
    SELECT * FROM (
        SELECT 'Revenue' as category, account_name, balance FROM monthly_balances WHERE account_type LIKE 'income%%'
        UNION ALL
        SELECT 'Cost of Goods Sold', account_name, -balance FROM monthly_balances WHERE account_type = 'expense_cogs'
        UNION ALL
        SELECT 'Operating Expenses', account_name, -balance FROM monthly_balances WHERE account_type = 'expense_operating'
        UNION ALL
        SELECT 'Other Expenses', account_name, -balance FROM monthly_balances WHERE account_type = 'expense_other'
    ) t
    ORDER BY
        CASE category
            WHEN 'Revenue' THEN 1
            WHEN 'Cost of Goods Sold' THEN 2
            WHEN 'Operating Expenses' THEN 3
            ELSE 4
        END
    """,
        "columns_json": [
            {"field": "category", "label": "Category", "type": "string"},
            {"field": "account_name", "label": "Account", "type": "string"},
            {"field": "balance", "label": "Amount", "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to", "label": "Date To", "type": "date"},
        ],
    },
    {
        "code": "ar_aging",
        "name": "AR Aging",
        "module": "accounting",
        "report_type": "query",
        "script": """
        SELECT
            p.name as party_name,
            i.number,
            i.doc_date,
            i.total_amount - COALESCE((
                SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa
                JOIN erp_accounting_payments py ON py.id = pa.payment_id
                WHERE pa.invoice_id = i.id AND pa.invoice_type = 'InflowInvoice' AND py.status = 'Posted'
            ), 0) as outstanding,
            DATEDIFF('{today}', i.doc_date) as days_outstanding,
            CASE WHEN DATEDIFF('{today}', i.doc_date) <= 30
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'InflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `0_30`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) BETWEEN 31 AND 60
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'InflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `31_60`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) BETWEEN 61 AND 90
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'InflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `61_90`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) > 90
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'InflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `over_90`
        FROM erp_accounting_inflow_invoices i
        JOIN erp_party_parties p ON i.party_id = p.id
        WHERE i.status IN ('Posted', 'Partial') AND i.org_id = :org_id
        HAVING outstanding > 0.01
        ORDER BY days_outstanding DESC
        """,
        "columns_json": [
            {"field": "party_name", "label": "Customer", "type": "string"},
            {"field": "number", "label": "Invoice #", "type": "string"},
            {"field": "doc_date", "label": "Date", "type": "date"},
            {"field": "outstanding", "label": "Outstanding", "type": "currency"},
            {"field": "days_outstanding", "label": "Days", "type": "number"},
            {"field": "0_30", "label": "0-30 Days", "type": "currency"},
            {"field": "31_60", "label": "31-60 Days", "type": "currency"},
            {"field": "61_90", "label": "61-90 Days", "type": "currency"},
            {"field": "over_90", "label": "90+ Days", "type": "currency"}
        ],
        "filters_json": [],
    },
    {
        "code": "ap_aging",
        "name": "AP Aging",
        "module": "accounting",
        "report_type": "query",
        "script": """
        SELECT
            p.name as party_name,
            i.number,
            i.doc_date,
            i.total_amount - COALESCE((
                SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa
                JOIN erp_accounting_payments py ON py.id = pa.payment_id
                WHERE pa.invoice_id = i.id AND pa.invoice_type = 'OutflowInvoice' AND py.status = 'Posted'
            ), 0) as outstanding,
            DATEDIFF('{today}', i.doc_date) as days_outstanding,
            CASE WHEN DATEDIFF('{today}', i.doc_date) <= 30
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'OutflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `0_30`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) BETWEEN 31 AND 60
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'OutflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `31_60`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) BETWEEN 61 AND 90
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'OutflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `61_90`,
            CASE WHEN DATEDIFF('{today}', i.doc_date) > 90
                THEN i.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments py ON py.id = pa.payment_id WHERE pa.invoice_id = i.id AND pa.invoice_type = 'OutflowInvoice' AND py.status = 'Posted'), 0)
                ELSE 0 END as `over_90`
        FROM erp_accounting_outflow_invoices i
        JOIN erp_party_parties p ON i.party_id = p.id
        WHERE i.status IN ('Posted', 'Partial') AND i.org_id = :org_id
        HAVING outstanding > 0.01
        ORDER BY days_outstanding DESC
        """,
        "columns_json": [
            {"field": "party_name", "label": "Supplier", "type": "string"},
            {"field": "number", "label": "Invoice #", "type": "string"},
            {"field": "doc_date", "label": "Date", "type": "date"},
            {"field": "outstanding", "label": "Outstanding", "type": "currency"},
            {"field": "days_outstanding", "label": "Days", "type": "number"},
            {"field": "0_30", "label": "0-30 Days", "type": "currency"},
            {"field": "31_60", "label": "31-60 Days", "type": "currency"},
            {"field": "61_90", "label": "61-90 Days", "type": "currency"},
            {"field": "over_90", "label": "90+ Days", "type": "currency"}
        ],
        "filters_json": [],
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
WHERE p.org_id = :org_id
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
    {
        "code": "general_ledger",
        "name": "General Ledger",
        "module": "accounting",
        "report_type": "query",
        "script": """SELECT 
  je.doc_date as date,
  je.number as reference,
  a.name as account,
  jl.debit,
  jl.credit,
  jl.description
FROM erp_accounting_entry_lines jl
JOIN erp_accounting_entries je ON je.id = jl.entry_id
JOIN erp_accounting_accounts a ON a.id = jl.account_id
WHERE je.org_id = :org_id
  AND je.status = 'Posted'
  AND (:date_from IS NULL OR je.doc_date >= :date_from)
  AND (:date_to IS NULL OR je.doc_date <= :date_to)
ORDER BY je.doc_date ASC, je.id ASC""",
        "columns_json": [
            {"field": "date",        "label": "Date",        "type": "date"},
            {"field": "reference",   "label": "Reference",   "type": "string"},
            {"field": "account",     "label": "Account",     "type": "string"},
            {"field": "description", "label": "Description", "type": "string"},
            {"field": "debit",       "label": "Debit",       "type": "currency"},
            {"field": "credit",      "label": "Credit",      "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date"},
            {"field": "date_to",   "label": "Date To",   "type": "date"},
        ],
    },
    {
        "code": "accounts_receivable",
        "name": "Accounts Receivable Aging",
        "module": "accounting",
        "report_type": "query",
        "script": """SELECT 
  c.name as customer,
  si.number as invoice_no,
  si.doc_date as date,
  si.total_amount,
  si.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments p ON p.id = pa.payment_id WHERE pa.invoice_id = si.id AND p.status = 'Posted'), 0) as balance
FROM erp_accounting_inflow_invoices si
JOIN erp_party_parties c ON c.id = si.party_id
WHERE si.org_id = :org_id AND si.status = 'Posted'
  AND (si.total_amount - COALESCE((SELECT SUM(pa.amount) FROM erp_accounting_payment_allocations pa JOIN erp_accounting_payments p ON p.id = pa.payment_id WHERE pa.invoice_id = si.id AND p.status = 'Posted'), 0)) > 0""",
        "columns_json": [
            {"field": "customer",     "label": "Customer",   "type": "string"},
            {"field": "invoice_no",   "label": "Invoice",    "type": "string"},
            {"field": "date",         "label": "Date",       "type": "date"},
            {"field": "total_amount", "label": "Total",      "type": "currency"},
            {"field": "balance",      "label": "Balance",    "type": "currency"},
        ],
        "filters_json": [],
    },
]



def run_seed(db: Session, org_id: int):
    Report = Aras.Model._registry["Report"] 
    for r in REPORTS:
        existing = Report.find(db, code=r["code"], org_id=org_id)
        if not existing:
            Report.create(db, {**r, "org_id": org_id})
        else:
            existing.update_self(db, {
                "name": r["name"],
                "script": r["script"],
                "report_type": r["report_type"],
                "columns_json": r["columns_json"],
                "filters_json": r["filters_json"],
            })
    print(f"[seed] report data seeded for company {org_id}.")
