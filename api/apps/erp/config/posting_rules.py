# Configurable via OrganizationPostingRule — ini hanya seed default
POSTING_RULE_DEFAULTS = {
    "retail": {
        "trx_in":  {"debit": "cash_bank",    "credit": "revenue"},
        "trx_out": {"debit": "expense",       "credit": "cash_bank"},
    },
    "coop": {
        "trx_in":  {"debit": "cash_bank",    "credit": "savings_liability"},
        "trx_out": {"debit": "loan_asset",    "credit": "cash_bank"},
    },
    "school": {
        "trx_in":  {"debit": "cash_bank",    "credit": "tuition_revenue"},
        "trx_out": {"debit": "ops_expense",   "credit": "cash_bank"},
    },
    "npo": {
        "trx_in":  {"debit": "cash_bank",    "credit": "fund_liability"},
        "trx_out": {"debit": "program_expense","credit": "cash_bank"},
    },
}
