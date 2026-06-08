# gemini-flash
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from core.report.services.report_service import ReportService
from apps.stock.models import Item, StockMovement, StockMovementLine
from plugins.commerce.models import Uom

# claude-sonnet-4-6
@ReportService.register("stock_summary")
def _stock_summary(db: Session, org_id: int, params: dict, columns: list):
    inbound_location = func.coalesce(StockMovementLine.to_location_id, StockMovement.to_location_id)
    outbound_location = func.coalesce(StockMovementLine.from_location_id, StockMovement.from_location_id)
    balance_expr = func.coalesce(
        func.sum(case((inbound_location.isnot(None), StockMovementLine.qty), else_=0)) -
        func.sum(case((outbound_location.isnot(None), StockMovementLine.qty), else_=0)),
        0
    )

    q = (db.query(
            Item.code.label("code"),
            Item.name.label("name"),
            func.coalesce(Uom.name, "").label("uom"),
            balance_expr.label("balance"),
        )
        .join(StockMovementLine, StockMovementLine.item_id == Item.id)
        .join(StockMovement, StockMovement.id == StockMovementLine.movement_id)
        .outerjoin(Uom, Uom.id == Item.uom_id)
        .filter(
            StockMovement.org_id == org_id,
            StockMovement.status == "Posted",
            StockMovement.deleted_at.is_(None),
            StockMovementLine.deleted_at.is_(None),
        )
        .group_by(Item.id, Item.code, Item.name, Uom.name)
        .having(balance_expr != 0)
        .order_by(Item.code, Item.name)
    )
    data = [row._asdict() for row in q.all()]
    return {"title": "Stock Summary", "data": data, "columns": columns}
