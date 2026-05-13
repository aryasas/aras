"""
Purpose: JSON-to-SQLAlchemy Query Builder for Reporting and Advanced Filtering.
Context: Tier 0 Utility. Pure logic for translating filters to SQL.
Rule: Zero framework dependencies (Removed inheritance from Service).
"""
from typing import Type, Any, Dict, List
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

class QueryBuilder:
    """
    Translates JSON filter objects into SQLAlchemy Query statements.
    """

    @classmethod
    def build_query(cls, model_class: Type[Any], filters: List[Dict[str, Any]]):
        """
        Example filters: [{"field": "price", "op": ">", "value": 100}]
        """
        stmt = select(model_class)
        
        conditions = []
        for f in filters:
            if not hasattr(model_class, f["field"]):
                continue
            field = getattr(model_class, f["field"])
            op = f["op"]
            val = f["value"]
            
            if op == "==": conditions.append(field == val)
            elif op == "!=": conditions.append(field != val)
            elif op == ">": conditions.append(field > val)
            elif op == "<": conditions.append(field < val)
            elif op == ">=": conditions.append(field >= val)
            elif op == "<=": conditions.append(field <= val)
            elif op == "like" or op == "ilike": conditions.append(field.ilike(f"%{val}%"))
            
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        return stmt

    @classmethod
    def execute(cls, db: Session, model_class: Type[Any], filters: List[Dict[str, Any]]):
        """Executes the built query and returns results."""
        stmt = cls.build_query(model_class, filters)
        return db.scalars(stmt).all()
