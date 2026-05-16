"""
International Chart of Accounts seed — 5-digit numbering, 3 group levels + leaf accounts.

Structure:
  Level 1 (root group):   10000, 20000, 30000, 40000, 50000 …
  Level 2 (sub-group):    11000, 12000, 21000 …
  Level 3 (detail group): 11100, 11200 …
  Level 4 (leaf account): 11110, 11120 …

Returns a dict of slug → AccAccount for key accounts used by seed helpers.
"""
from sqlalchemy.orm import Session
from core import Aras

# fmt: (code, name, account_type, is_group, parent_code, slug_key | None)
# parent_code=None → root node
_COA: list[tuple] = [
    # ═══════════════════════════════════════════════════════════
    # 1 — ASSETS
    # ═══════════════════════════════════════════════════════════
    ("10000", "Assets",                         "view",              True,  None,    None),
    # 1.1 Current Assets
    ("11000", "Current Assets",                 "asset_current",     True,  "10000", None),
    ("11100", "Cash & Cash Equivalents",        "asset_current",     True,  "11000", None),
    ("11110", "Petty Cash",                     "asset_current",     False, "11100", "petty_cash"),
    ("11120", "Cash on Hand",                   "asset_current",     False, "11100", "cash"),
    ("11130", "Cash in Bank - Checking",        "asset_current",     False, "11100", "bank"),
    ("11140", "Cash in Bank - Savings",         "asset_current",     False, "11100", None),
    ("11200", "Short-term Investments",         "asset_current",     True,  "11000", None),
    ("11210", "Marketable Securities",          "asset_current",     False, "11200", None),
    ("11300", "Receivables",                    "asset_current",     True,  "11000", None),
    ("11310", "Accounts Receivable - Trade",    "asset_current",     False, "11300", "receivable"),
    ("11320", "Notes Receivable",               "asset_current",     False, "11300", None),
    ("11330", "Other Receivables",              "asset_current",     False, "11300", None),
    ("11400", "Inventories",                    "asset_current",     True,  "11000", None),
    ("11410", "Raw Materials",                  "asset_current",     False, "11400", None),
    ("11420", "Work in Progress",               "asset_current",     False, "11400", None),
    ("11430", "Finished Goods",                 "asset_current",     False, "11400", "inventory"),
    ("11440", "Merchandise Inventory",          "asset_current",     False, "11400", None),
    ("11500", "Prepaid Expenses",               "asset_current",     True,  "11000", None),
    ("11510", "Prepaid Insurance",              "asset_current",     False, "11500", None),
    ("11520", "Prepaid Rent",                   "asset_current",     False, "11500", None),
    ("11530", "Prepaid Other",                  "asset_current",     False, "11500", None),
    # 1.2 Non-current Assets
    ("12000", "Non-current Assets",             "asset_fixed",       True,  "10000", None),
    ("12100", "Property, Plant & Equipment",    "asset_fixed",       True,  "12000", None),
    ("12110", "Land",                           "asset_fixed",       False, "12100", None),
    ("12120", "Buildings",                      "asset_fixed",       False, "12100", None),
    ("12130", "Machinery & Equipment",          "asset_fixed",       False, "12100", None),
    ("12140", "Furniture & Fixtures",           "asset_fixed",       False, "12100", None),
    ("12150", "Vehicles",                       "asset_fixed",       False, "12100", None),
    ("12190", "Accumulated Depreciation - PPE", "asset_fixed",       False, "12100", None),
    ("12200", "Intangible Assets",              "asset_other",       True,  "12000", None),
    ("12210", "Patents & Trademarks",           "asset_other",       False, "12200", None),
    ("12220", "Goodwill",                       "asset_other",       False, "12200", None),
    ("12230", "Software & Licenses",            "asset_other",       False, "12200", None),
    ("12240", "Accumulated Amortization",       "asset_other",       False, "12200", None),
    ("12300", "Long-term Investments",          "asset_other",       True,  "12000", None),
    ("12310", "Equity Investments",             "asset_other",       False, "12300", None),
    ("12320", "Long-term Notes Receivable",     "asset_other",       False, "12300", None),
    ("12400", "Other Non-current Assets",       "asset_other",       True,  "12000", None),
    ("12410", "Deposits",                       "asset_other",       False, "12400", None),
    ("12420", "Deferred Tax Asset",             "asset_other",       False, "12400", None),

    # ═══════════════════════════════════════════════════════════
    # 2 — LIABILITIES
    # ═══════════════════════════════════════════════════════════
    ("20000", "Liabilities",                    "view",              True,  None,    None),
    # 2.1 Current Liabilities
    ("21000", "Current Liabilities",            "liability_current", True,  "20000", None),
    ("21100", "Payables",                       "liability_current", True,  "21000", None),
    ("21110", "Accounts Payable - Trade",       "liability_current", False, "21100", "payable"),
    ("21120", "Notes Payable",                  "liability_current", False, "21100", None),
    ("21130", "Accrued Liabilities",            "liability_current", False, "21100", None),
    ("21200", "Short-term Borrowings",          "liability_current", True,  "21000", None),
    ("21210", "Short-term Bank Loans",          "liability_current", False, "21200", None),
    ("21220", "Current Portion - Long-term",    "liability_current", False, "21200", None),
    ("21300", "Tax Liabilities",                "liability_current", True,  "21000", None),
    ("21310", "Sales Tax / VAT Payable",        "liability_current", False, "21300", "tax_output"),
    ("21320", "Income Tax Payable",             "liability_current", False, "21300", None),
    ("21330", "Withholding Tax Payable",        "liability_current", False, "21300", None),
    ("21400", "Wages & Payroll Payable",        "liability_current", True,  "21000", None),
    ("21410", "Wages Payable",                  "liability_current", False, "21400", None),
    ("21420", "Payroll Tax Payable",            "liability_current", False, "21400", None),
    ("21500", "Deferred Revenue",               "liability_current", True,  "21000", None),
    ("21510", "Customer Deposits",              "liability_current", False, "21500", None),
    ("21520", "Unearned Revenue",               "liability_current", False, "21500", None),
    # 2.2 Non-current Liabilities
    ("22000", "Non-current Liabilities",        "liability_long",    True,  "20000", None),
    ("22100", "Long-term Debt",                 "liability_long",    True,  "22000", None),
    ("22110", "Bank Loans - Long-term",         "liability_long",    False, "22100", None),
    ("22120", "Bonds Payable",                  "liability_long",    False, "22100", None),
    ("22200", "Other Non-current Liabilities",  "liability_long",    True,  "22000", None),
    ("22210", "Deferred Tax Liability",         "liability_long",    False, "22200", None),
    ("22220", "Lease Obligations",              "liability_long",    False, "22200", None),

    # ═══════════════════════════════════════════════════════════
    # 3 — EQUITY
    # ═══════════════════════════════════════════════════════════
    ("30000", "Equity",                         "view",              True,  None,    None),
    ("31000", "Paid-in Capital",                "equity",            True,  "30000", None),
    ("31100", "Common Stock / Ordinary Shares", "equity",            True,  "31000", None),
    ("31110", "Issued Capital",                 "equity",            False, "31100", None),
    ("31120", "Additional Paid-in Capital",     "equity",            False, "31100", None),
    ("31200", "Preferred Stock",                "equity",            True,  "31000", None),
    ("31210", "Preferred Shares",               "equity",            False, "31200", None),
    ("32000", "Retained Earnings",              "equity",            True,  "30000", None),
    ("32100", "Retained Earnings",              "equity",            True,  "32000", None),
    ("32110", "Retained Earnings - Prior Years","equity",            False, "32100", None),
    ("32120", "Current Year Earnings",          "equity",            False, "32100", None),
    ("32200", "Reserves",                       "equity",            True,  "32000", None),
    ("32210", "Legal Reserve",                  "equity",            False, "32200", None),
    ("32220", "General Reserve",                "equity",            False, "32200", None),
    ("33000", "Other Equity",                   "equity",            True,  "30000", None),
    ("33100", "Treasury Stock",                 "equity",            True,  "33000", None),
    ("33110", "Treasury Shares",                "equity",            False, "33100", None),
    ("33200", "Other Comprehensive Income",     "equity",            True,  "33000", None),
    ("33210", "Foreign Currency Translation",   "equity",            False, "33200", None),
    ("33220", "Unrealized Gains/Losses",        "equity",            False, "33200", None),

    # ═══════════════════════════════════════════════════════════
    # 4 — REVENUE / INCOME
    # ═══════════════════════════════════════════════════════════
    ("40000", "Revenue",                        "view",              True,  None,    None),
    ("41000", "Operating Revenue",              "income_operating",  True,  "40000", None),
    ("41100", "Sales Revenue",                  "income_operating",  True,  "41000", None),
    ("41110", "Product Sales",                  "income_operating",  False, "41100", "revenue"),
    ("41120", "Service Revenue",                "income_operating",  False, "41100", None),
    ("41130", "Subscription Revenue",           "income_operating",  False, "41100", None),
    ("41200", "Sales Deductions",               "income_operating",  True,  "41000", None),
    ("41210", "Sales Returns",                  "income_operating",  False, "41200", None),
    ("41220", "Sales Discounts",                "income_operating",  False, "41200", None),
    ("41230", "Sales Allowances",               "income_operating",  False, "41200", None),
    ("42000", "Non-operating Income",           "income_other",      True,  "40000", None),
    ("42100", "Financial Income",               "income_other",      True,  "42000", None),
    ("42110", "Interest Income",                "income_other",      False, "42100", None),
    ("42120", "Dividend Income",                "income_other",      False, "42100", None),
    ("42200", "Gain on Disposal of Assets",     "income_other",      True,  "42000", None),
    ("42210", "Gain on Fixed Asset Disposal",   "income_other",      False, "42200", None),
    ("42300", "Other Income",                   "income_other",      True,  "42000", None),
    ("42310", "Miscellaneous Income",           "income_other",      False, "42300", None),
    ("42320", "Rental Income",                  "income_other",      False, "42300", None),

    # ═══════════════════════════════════════════════════════════
    # 5 — COST OF GOODS SOLD
    # ═══════════════════════════════════════════════════════════
    ("50000", "Cost of Goods Sold",             "view",              True,  None,    None),
    ("51000", "Cost of Sales",                  "expense_cogs",      True,  "50000", None),
    ("51100", "Direct Product Cost",            "expense_cogs",      True,  "51000", None),
    ("51110", "Cost of Goods Sold",             "expense_cogs",      False, "51100", "cogs"),
    ("51120", "Inventory Variance",             "expense_cogs",      False, "51100", "variance"),
    ("51130", "Purchase Returns",               "expense_cogs",      False, "51100", None),
    ("51200", "Direct Labor",                   "expense_cogs",      True,  "51000", None),
    ("51210", "Direct Wages",                   "expense_cogs",      False, "51200", None),
    ("51220", "Overtime - Production",          "expense_cogs",      False, "51200", None),
    ("51300", "Manufacturing Overhead",         "expense_cogs",      True,  "51000", None),
    ("51310", "Factory Rent",                   "expense_cogs",      False, "51300", None),
    ("51320", "Factory Utilities",              "expense_cogs",      False, "51300", None),
    ("51330", "Depreciation - Production",      "expense_cogs",      False, "51300", None),

    # ═══════════════════════════════════════════════════════════
    # 6 — OPERATING EXPENSES
    # ═══════════════════════════════════════════════════════════
    ("60000", "Operating Expenses",             "view",              True,  None,    None),
    ("61000", "Selling & Distribution",         "expense_operating", True,  "60000", None),
    ("61100", "Marketing & Advertising",        "expense_operating", True,  "61000", None),
    ("61110", "Advertising & Promotions",       "expense_operating", False, "61100", None),
    ("61120", "Social Media & Digital Mktg",    "expense_operating", False, "61100", None),
    ("61200", "Sales Team Expenses",            "expense_operating", True,  "61000", None),
    ("61210", "Sales Commissions",              "expense_operating", False, "61200", None),
    ("61220", "Sales Travel & Entertainment",   "expense_operating", False, "61200", None),
    ("61300", "Delivery & Logistics",           "expense_operating", True,  "61000", None),
    ("61310", "Freight Out",                    "expense_operating", False, "61300", None),
    ("61320", "Packaging",                      "expense_operating", False, "61300", None),
    ("62000", "General & Administrative",       "expense_operating", True,  "60000", None),
    ("62100", "Personnel Expenses",             "expense_operating", True,  "62000", None),
    ("62110", "Salaries & Wages",               "expense_operating", False, "62100", None),
    ("62120", "Employee Benefits",              "expense_operating", False, "62100", None),
    ("62130", "Staff Training",                 "expense_operating", False, "62100", None),
    ("62200", "Office Expenses",                "expense_operating", True,  "62000", None),
    ("62210", "Office Supplies",                "expense_operating", False, "62200", None),
    ("62220", "Telecommunications",             "expense_operating", False, "62200", None),
    ("62230", "Postage & Courier",              "expense_operating", False, "62200", None),
    ("62300", "Facilities",                     "expense_operating", True,  "62000", None),
    ("62310", "Rent Expense",                   "expense_operating", False, "62300", None),
    ("62320", "Utilities Expense",              "expense_operating", False, "62300", None),
    ("62330", "Cleaning & Maintenance",         "expense_operating", False, "62300", None),
    ("62400", "Depreciation & Amortization",    "expense_operating", True,  "62000", None),
    ("62410", "Depreciation - Equipment",       "expense_operating", False, "62400", None),
    ("62420", "Amortization - Intangibles",     "expense_operating", False, "62400", None),
    ("62500", "Insurance & Legal",              "expense_operating", True,  "62000", None),
    ("62510", "Insurance Premiums",             "expense_operating", False, "62500", None),
    ("62520", "Legal & Professional Fees",      "expense_operating", False, "62500", None),

    # ═══════════════════════════════════════════════════════════
    # 7 — FINANCIAL & OTHER EXPENSES
    # ═══════════════════════════════════════════════════════════
    ("70000", "Financial & Other Expenses",     "view",              True,  None,    None),
    ("71000", "Financial Expenses",             "expense_other",     True,  "70000", None),
    ("71100", "Interest & Finance Charges",     "expense_other",     True,  "71000", None),
    ("71110", "Interest Expense - Bank",        "expense_other",     False, "71100", None),
    ("71120", "Bank Charges & Fees",            "expense_other",     False, "71100", None),
    ("71130", "Foreign Exchange Loss",          "expense_other",     False, "71100", None),
    ("72000", "Non-operating Expenses",         "expense_other",     True,  "70000", None),
    ("72100", "Loss on Disposal of Assets",     "expense_other",     True,  "72000", None),
    ("72110", "Loss on Fixed Asset Disposal",   "expense_other",     False, "72100", None),
    ("72200", "Other Expenses",                 "expense_other",     True,  "72000", None),
    ("72210", "Miscellaneous Expenses",         "expense_other",     False, "72200", None),
    ("72220", "Fines & Penalties",              "expense_other",     False, "72200", None),
    ("73000", "Income Tax Expense",             "expense_other",     True,  "70000", None),
    ("73100", "Tax Expense",                    "expense_other",     True,  "73000", None),
    ("73110", "Current Tax Expense",            "expense_other",     False, "73100", None),
    ("73120", "Deferred Tax Expense",           "expense_other",     False, "73100", None),
]


def seed_coa(db: Session, org_id: int) -> dict:
    """
    Upsert all CoA rows for org_id.
    Returns dict of slug → Account for key accounts used by seed helpers.
    """
    # Get Account model from registry
    Account = Aras.Model._registry["Account"]
    
    # First pass: build code → (row, slug) index & create/update all
    code_map: dict[str, Account] = {}
    slugs: dict[str, Account] = {}

    # Insert in definition order (parents first)
    for code, name, acct_type, is_group, parent_code, slug in _COA:
        parent_id = code_map[parent_code].id if parent_code and parent_code in code_map else None
        acc, _ = Account.get_or_create(
            db, # Pass the db session
            {
                "name": name,
                "account_type": acct_type,
                "is_group": is_group,
                "parent_id": parent_id,
                "org_id": org_id,
            },
            code=code,
            org_id=org_id,
        )
        # keep name/type/is_group current (idempotent update)
        changed = False
        if acc.name != name:
            acc.name = name; changed = True
        if acc.account_type != acct_type:
            acc.account_type = acct_type; changed = True
        if acc.is_group != is_group:
            acc.is_group = is_group; changed = True
        if acc.parent_id != parent_id:
            acc.parent_id = parent_id; changed = True
        if changed:
            db.add(acc) # Use db.add


        code_map[code] = acc
        if slug:
            slugs[slug] = acc

    db.flush()
    return slugs
