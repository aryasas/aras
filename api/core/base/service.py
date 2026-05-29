"""
Purpose: Standardized base class for all Business Logic services.
Context: Level 2 Base.
Impact: Provides unified CRUD patterns with RBAC and Audit hooks.
"""
import logging
from typing import List, Type, Any, Optional, Dict
from sqlalchemy.orm import Session
from .aras import Aras
from .model import Model
from ..logic.permissions import RBAC
from ..exceptions import PermissionDeniedException, ResourceNotFoundException

logger = logging.getLogger(__name__)

# claude-sonnet-4-6
class Service(Aras):
    """
    Base Service class providing standard CRUD operations.
    Subclasses should define 'model_class'.
    """
    model_class: Type[Model] = None

    @classmethod
    def _check_permission(cls, db: Session, user: Any, action: str):
        """Standard RBAC check."""
        if not cls.model_class:
            return
        if not RBAC.has_permission(db, user, cls.model_class.__tablename__, action):
            raise PermissionDeniedException(f"Not enough permissions to {action} {cls.model_class.__tablename__}")

    @classmethod
    def list(cls, db: Session, user: Any, filters: Optional[List[Dict]] = None, page: int = 1, per_page: int = 20, order_by: Optional[str] = None, desc: bool = True):
        """Lists records with RBAC check."""
        cls._check_permission(db, user, "READ")
        return cls.model_class.paginate(db, filters=filters, page=page, per_page=per_page, order_by=order_by, desc=desc)

    @classmethod
    def get(cls, db: Session, user: Any, id: Any):
        """Fetches a single record with RBAC check."""
        cls._check_permission(db, user, "READ")
        item = cls.model_class.get(db, id)
        if not item:
            raise ResourceNotFoundException(f"{cls.model_class.__name__} not found")
        return item

    @classmethod
    def create(cls, db: Session, user: Any, payload: Dict[str, Any]):
        """Creates a new record with RBAC check."""
        cls._check_permission(db, user, "CREATE")
        item = cls.model_class.create(db, payload, user_id=user.id)
        db.commit()
        return item

    @classmethod
    def update(cls, db: Session, user: Any, id: Any, payload: Dict[str, Any]):
        """Updates an existing record with RBAC check."""
        cls._check_permission(db, user, "UPDATE")
        item = cls.get(db, user, id)
        item.update_self(db, payload, user_id=user.id)
        db.commit()
        return item

    @classmethod
    def delete(cls, db: Session, user: Any, id: Any):
        """Deletes a record with RBAC check."""
        cls._check_permission(db, user, "DELETE")
        item = cls.get(db, user, id)
        item.delete_self(db, user_id=user.id)
        db.commit()
        return True
