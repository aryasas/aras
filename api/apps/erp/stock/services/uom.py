from sqlalchemy.orm import Session
from ..models import ItemUom

class UomService:
    @staticmethod
    def convert_qty(db: Session, item_id: int, qty: float, from_uom_id: int, to_uom_id: int) -> float:
        if from_uom_id == to_uom_id or from_uom_id is None or to_uom_id is None:
            return qty
        src = db.query(ItemUom).filter_by(item_id=item_id, uom_id=from_uom_id).first()
        dst = db.query(ItemUom).filter_by(item_id=item_id, uom_id=to_uom_id).first()
        from_factor = src.factor if src else 1.0
        to_factor = dst.factor if dst else 1.0
        if to_factor == 0:
            return qty
        return qty * from_factor / to_factor

    @staticmethod
    def get_factor(db: Session, item_id: int, uom_id: int) -> float:
        rec = db.query(ItemUom).filter_by(item_id=item_id, uom_id=uom_id).first()
        return rec.factor if rec else 1.0
