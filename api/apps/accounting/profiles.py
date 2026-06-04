from typing import Optional


# Default vocabulary per profile — user dapat override via OrganizationVocabulary
PROFILE_DEFAULTS = {
    "general": {
        "display_name": "General",
        "description": "Neutral terms for any organization.",
        "labels": {"trx_in": "Inflow", "trx_out": "Outflow", "party": "Party", "pot": "Transaction Point"},
    },
    "company": {
        "display_name": "Company / Trade",
        "description": "Buys and sells stock with standard trade terms.",
        "labels": {"trx_in": "Sales", "trx_out": "Purchase", "party": "Customer", "pot": "Point of Sale"},
    },
    "retail": {
        "display_name": "Retail Store",
        "description": "Shop-style trading with sales and purchase flows.",
        "labels": {"trx_in": "Sales", "trx_out": "Purchase", "party": "Customer", "pot": "Point of Sale"},
    },
    "restaurant": {
        "display_name": "Restaurant / Cafe",
        "description": "Food service transactions with cashier-based operations.",
        "labels": {"trx_in": "Sales", "trx_out": "Purchase", "party": "Customer", "pot": "Cashier"},
    },
    "manufacturing": {
        "display_name": "Manufacturing",
        "description": "Production-oriented trading with material purchases.",
        "labels": {"trx_in": "Sales", "trx_out": "Purchase / Material", "party": "Customer", "pot": "Order Desk"},
    },
    "school": {
        "display_name": "School",
        "description": "Education flows using tuition and expenditure terms.",
        "labels": {"trx_in": "Tuition", "trx_out": "Expenditure", "party": "Student", "pot": "Payment Counter"},
    },
    "coop": {
        "display_name": "Cooperative",
        "description": "Member-based savings and loan operations.",
        "labels": {"trx_in": "Savings", "trx_out": "Loan", "party": "Member", "pot": "Teller"},
    },
    "npo": {
        "display_name": "NGO / Yayasan",
        "description": "Nonprofit flows using donation and program cost terms.",
        "labels": {"trx_in": "Donation", "trx_out": "Program Cost", "party": "Donor", "pot": "Collection Point"},
    },
    "library": {
        "display_name": "Library",
        "description": "Membership-based operations with circulation service points.",
        "labels": {"trx_in": "Membership", "trx_out": "Procurement", "party": "Member", "pot": "Circulation Desk"},
    },
    "hospital": {
        "display_name": "Hospital / Clinic",
        "description": "Healthcare billing and procurement vocabulary.",
        "labels": {"trx_in": "Patient Bill", "trx_out": "Procurement", "party": "Patient", "pot": "Registration"},
    },
    "government": {
        "display_name": "Government Office",
        "description": "Public-service revenue and expenditure vocabulary.",
        "labels": {"trx_in": "Revenue", "trx_out": "Expenditure", "party": "Citizen", "pot": "Service Counter"},
    },
}


# claude-opus-4-8
def get_profile_definition(profile: Optional[str]) -> dict:
    return PROFILE_DEFAULTS.get(profile or "general", PROFILE_DEFAULTS["general"])


# claude-opus-4-8
def get_profile_labels(profile: Optional[str]) -> dict[str, str]:
    return dict(get_profile_definition(profile)["labels"])


# claude-opus-4-8
def get_profile_catalog() -> list[dict]:
    return [
        {
            "key": key,
            "display_name": value["display_name"],
            "description": value["description"],
            "labels": dict(value["labels"]),
        }
        for key, value in PROFILE_DEFAULTS.items()
    ]
