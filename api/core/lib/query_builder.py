"""
Purpose: JSON-to-SQLAlchemy Query Builder for Reporting and Advanced Filtering.
Context: Level 3 Utility. Used by the BI/Reporting layer.
Impact: Standardizes how the frontend requests complex filtered data.
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
