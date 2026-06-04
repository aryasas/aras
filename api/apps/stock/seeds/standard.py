# claude-opus-4-8
from plugins.commerce.models import Uom


# claude-opus-4-8
def seed_trade_uoms(db):
    for name in (
        "pcs",
        "box",
        "kg",
        "liter",
    ):
        Uom.get_or_create(db, {"name": name}, name=name)
    db.flush()


seed_trade_uoms.key = "trade_uoms"
seed_trade_uoms.label = "Trade Units"
seed_trade_uoms.optional = False
