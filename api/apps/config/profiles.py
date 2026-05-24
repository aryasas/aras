# Default vocabulary per profile — user dapat override via OrganizationVocabulary
PROFILE_DEFAULTS = {
    "general":    {"trx_in": "Inflow",        "trx_out": "Outflow",      "party": "Party",    "pot": "Transaction Point"},
    "retail":     {"trx_in": "Sales",         "trx_out": "Purchase",     "party": "Customer", "pot": "Point of Sale"},
    "school":     {"trx_in": "Tuition",       "trx_out": "Expenditure",  "party": "Student",  "pot": "Payment Counter"},
    "coop":       {"trx_in": "Savings",       "trx_out": "Loan",         "party": "Member",   "pot": "Teller"},
    "npo":        {"trx_in": "Donation",      "trx_out": "Program Cost", "party": "Donor",    "pot": "Collection Point"},
    "library":    {"trx_in": "Membership",    "trx_out": "Procurement",  "party": "Member",   "pot": "Circulation Desk"},
    "hospital":   {"trx_in": "Patient Bill",  "trx_out": "Procurement",  "party": "Patient",  "pot": "Registration"},
    "government": {"trx_in": "Revenue",       "trx_out": "Expenditure",  "party": "Citizen",  "pot": "Service Counter"},
}
