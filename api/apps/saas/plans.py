# claude-sonnet-4-6
DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "plan_key": "free",
        "name": "Free",
        "price": 0,
        "currency": "IDR",
        "max_users": 1,
        "max_branches": 1,
        "max_transactions": 50,
        "max_products": 30,
        "storage_mb": 256,
        "active_modules": ["pos"],
        "api_access": False,
        "sort_order": 0,
        "features": {
            "included": [
                "Modul POS",
                "50 transaksi/bulan",
                "30 produk",
                "Laporan harian dasar",
            ],
        },
    },
    {
        "plan_key": "lite",
        "name": "Lite",
        "price": 50000,
        "currency": "IDR",
        "max_users": 3,
        "max_branches": 1,
        "max_transactions": -1,
        "max_products": 500,
        "storage_mb": 512,
        "active_modules": ["pos", "stock", "receivable"],
        "api_access": False,
        "sort_order": 1,
        "features": {
            "included": [
                "Modul POS + Stok + Hutang Piutang",
                "Transaksi unlimited",
                "500 produk",
                "Laporan bulanan",
                "Export PDF",
            ],
        },
    },
    {
        "plan_key": "growth",
        "name": "Growth",
        "price": 299000,
        "currency": "IDR",
        "max_users": 10,
        "max_branches": 2,
        "max_transactions": -1,
        "max_products": -1,
        "storage_mb": 3072,
        "active_modules": ["pos", "stock", "receivable", "accounting"],
        "api_access": False,
        "sort_order": 2,
        "features": {
            "included": [
                "Semua fitur Lite",
                "Accounting penuh (laba rugi, neraca)",
                "Produk unlimited",
                "Hingga 2 cabang",
                "Support chat",
            ],
        },
    },
    {
        "plan_key": "business",
        "name": "Business",
        "price": 599000,
        "currency": "IDR",
        "max_users": 25,
        "max_branches": -1,
        "max_transactions": -1,
        "max_products": -1,
        "storage_mb": 10240,
        "active_modules": ["pos", "stock", "receivable", "accounting"],
        "api_access": True,
        "sort_order": 3,
        "features": {
            "included": [
                "Semua fitur Growth",
                "Cabang unlimited",
                "25 pengguna",
                "API access",
                "Prioritas support",
                "Onboarding",
            ],
        },
    },
]


def seed_default_plans(db):
    from .models import Plan

    for plan_data in DEFAULT_SUBSCRIPTION_PLANS:
        plan = db.query(Plan).filter_by(plan_key=plan_data["plan_key"]).first()
        if not plan:
            plan = Plan(**plan_data)
            plan.is_active = True
            db.add(plan)

    db.commit()
