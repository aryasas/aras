# claude-sonnet-4-6
from sqlalchemy.orm import Session
from core import Aras
from datetime import datetime, timedelta, timezone

TODAY = datetime.now(timezone.utc).date()
DATE_FROM = (TODAY - timedelta(days=365)).isoformat()
DATE_TO = TODAY.isoformat()

REPORTS = [
    {
        "code": "sales_summary",
        "name": "Sales Summary",
        "module": "accounting",
        "report_type": "builtin",
        "linked_doctype": "InflowInvoice",
        "columns_json": [
            {"field": "invoice_no", "label": "Invoice No", "type": "string"},
            {"field": "customer",   "label": "Customer",   "type": "string"},
            {"field": "date",       "label": "Date",       "type": "date"},
            {"field": "subtotal",   "label": "Subtotal",   "type": "currency"},
            {"field": "tax",        "label": "Tax",        "type": "currency"},
            {"field": "total",      "label": "Total",      "type": "currency"},
            {"field": "status",     "label": "Status",     "type": "string"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to",   "label": "Date To",   "type": "date", "default": DATE_TO},
            {"field": "status",    "label": "Status",    "type": "select",
             "options": [("", "All"), ("Draft", "Draft"), ("Posted", "Posted"),
                         ("Paid", "Paid"), ("Cancelled", "Cancelled")]},
        ],
    },
    {
        "code": "purchase_summary",
        "name": "Purchase Summary",
        "module": "accounting",
        "report_type": "builtin",
        "linked_doctype": "OutflowInvoice",
        "columns_json": [
            {"field": "invoice_no", "label": "Bill No",   "type": "string"},
            {"field": "vendor",     "label": "Vendor",    "type": "string"},
            {"field": "date",       "label": "Date",      "type": "date"},
            {"field": "subtotal",   "label": "Subtotal",  "type": "currency"},
            {"field": "tax",        "label": "Tax",       "type": "currency"},
            {"field": "total",      "label": "Total",     "type": "currency"},
            {"field": "status",     "label": "Status",    "type": "string"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to",   "label": "Date To",   "type": "date", "default": DATE_TO},
            {"field": "status",    "label": "Status",    "type": "select",
             "options": [("", "All"), ("Draft", "Draft"), ("Posted", "Posted"),
                         ("Paid", "Paid"), ("Cancelled", "Cancelled")]},
        ],
    },
    {
        "code": "trial_balance",
        "name": "Trial Balance",
        "module": "accounting",
        "report_type": "builtin",
        "columns_json": [
            {"field": "account_code",  "label": "Account Code", "type": "string"},
            {"field": "account_name",  "label": "Account Name", "type": "string"},
            {"field": "total_debit",   "label": "Debit",        "type": "currency"},
            {"field": "total_credit",  "label": "Credit",       "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to",   "label": "Date To",   "type": "date", "default": DATE_TO},
        ],
    },
    {
        "code": "profit_and_loss",
        "name": "Profit & Loss",
        "module": "accounting",
        "report_type": "builtin",
        "columns_json": [
            {"field": "category",      "label": "Category", "type": "string"},
            {"field": "account_name",  "label": "Account",  "type": "string"},
            {"field": "balance",       "label": "Amount",   "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to",   "label": "Date To",   "type": "date", "default": DATE_TO},
        ],
    },
    {
        "code": "ar_aging",
        "name": "AR Aging",
        "module": "accounting",
        "report_type": "builtin",
        "linked_doctype": "InflowInvoice",
        "columns_json": [
            {"field": "party_name",       "label": "Customer",    "type": "string"},
            {"field": "number",           "label": "Invoice #",   "type": "string"},
            {"field": "doc_date",         "label": "Date",        "type": "date"},
            {"field": "outstanding",      "label": "Outstanding", "type": "currency"},
            {"field": "days_outstanding", "label": "Days",        "type": "number"},
            {"field": "0_30",             "label": "0-30 Days",   "type": "currency"},
            {"field": "31_60",            "label": "31-60 Days",  "type": "currency"},
            {"field": "61_90",            "label": "61-90 Days",  "type": "currency"},
            {"field": "over_90",          "label": "90+ Days",    "type": "currency"},
        ],
        "filters_json": [],
    },
    {
        "code": "ap_aging",
        "name": "AP Aging",
        "module": "accounting",
        "report_type": "builtin",
        "linked_doctype": "OutflowInvoice",
        "columns_json": [
            {"field": "party_name",       "label": "Supplier",    "type": "string"},
            {"field": "number",           "label": "Invoice #",   "type": "string"},
            {"field": "doc_date",         "label": "Date",        "type": "date"},
            {"field": "outstanding",      "label": "Outstanding", "type": "currency"},
            {"field": "days_outstanding", "label": "Days",        "type": "number"},
            {"field": "0_30",             "label": "0-30 Days",   "type": "currency"},
            {"field": "31_60",            "label": "31-60 Days",  "type": "currency"},
            {"field": "61_90",            "label": "61-90 Days",  "type": "currency"},
            {"field": "over_90",          "label": "90+ Days",    "type": "currency"},
        ],
        "filters_json": [],
    },
    {
        "code": "cash_flow",
        "name": "Cash Flow",
        "module": "accounting",
        "report_type": "builtin",
        "columns_json": [
            {"field": "opening_bank_balance", "label": "Opening Bank Balance", "type": "currency"},
            {"field": "cash_inflows", "label": "Cash Inflows", "type": "currency"},
            {"field": "cash_outflows", "label": "Cash Outflows", "type": "currency"},
            {"field": "net_cash_movement", "label": "Net Cash Movement", "type": "currency"},
            {"field": "closing_bank_balance", "label": "Closing Bank Balance", "type": "currency"},
            {"field": "scope_note", "label": "Scope", "type": "string"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to", "label": "Date To", "type": "date", "default": DATE_TO},
        ],
    },
    {
        "code": "stock_summary",
        "name": "Stock Summary",
        "module": "stock",
        "report_type": "builtin",
        "linked_doctype": "Item",
        "columns_json": [
            {"field": "code",    "label": "Code",    "type": "string"},
            {"field": "name",    "label": "Item",    "type": "string"},
            {"field": "uom",     "label": "UoM",     "type": "string"},
            {"field": "balance", "label": "Balance", "type": "number"},
        ],
        "filters_json": [],
    },
    {
        "code": "general_ledger",
        "name": "General Ledger",
        "module": "accounting",
        "report_type": "builtin",
        "columns_json": [
            {"field": "date",        "label": "Date",        "type": "date"},
            {"field": "reference",   "label": "Reference",   "type": "string"},
            {"field": "account",     "label": "Account",     "type": "string"},
            {"field": "description", "label": "Description", "type": "string"},
            {"field": "debit",       "label": "Debit",       "type": "currency"},
            {"field": "credit",      "label": "Credit",      "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to",   "label": "Date To",   "type": "date", "default": DATE_TO},
        ],
    },
    {
        "code": "accounts_receivable",
        "name": "Accounts Receivable Aging",
        "module": "accounting",
        "report_type": "builtin",
        "linked_doctype": "InflowInvoice",
        "columns_json": [
            {"field": "customer",     "label": "Customer", "type": "string"},
            {"field": "invoice_no",   "label": "Invoice",  "type": "string"},
            {"field": "date",         "label": "Date",     "type": "date"},
            {"field": "total_amount", "label": "Total",    "type": "currency"},
            {"field": "balance",      "label": "Balance",  "type": "currency"},
        ],
        "filters_json": [],
    },
    {
        "code": "tax_summary",
        "name": "Tax Summary",
        "module": "accounting",
        "report_type": "builtin",
        "columns_json": [
            {"field": "period", "label": "Period", "type": "string"},
            {"field": "direction", "label": "Direction", "type": "string"},
            {"field": "tax_rate", "label": "Tax Rate", "type": "string"},
            {"field": "rate", "label": "Rate %", "type": "number"},
            {"field": "taxable_base", "label": "Taxable Base", "type": "currency"},
            {"field": "tax_amount", "label": "Tax Amount", "type": "currency"},
        ],
        "filters_json": [
            {"field": "date_from", "label": "Date From", "type": "date", "default": DATE_FROM},
            {"field": "date_to", "label": "Date To", "type": "date", "default": DATE_TO},
        ],
    },
]


# claude-sonnet-4-6
def run_seed(db: Session, org_id: int):
    Report = Aras.Model._registry["Report"]
    count = 0
    for r in REPORTS:
        try:
            existing = Report.find(db, code=r["code"], org_id=org_id)
            data = {**r, "org_id": org_id}
            if not existing:
                Report.create(db, data)
            else:
                existing.update_self(db, data)
            count += 1
        except Exception as e:
            print(f"[seed error] {r['code']}: {e}")
    db.flush()
    print(f"[seed] {count}/{len(REPORTS)} reports seeded for org {org_id}.")
