"""
Purpose: Generic factory for generating standardized CRUD routes for any Aras Model.
Context: Level 3 Utility. Used by register_app_routes.
Impact: Automates API exposure with built-in validation, permissions, and metadata.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Type, Any, Optional
from pydantic import create_model

from .database import get_db
# Note: In a real implementation, we would use Aras.get_current_user etc.
# For now, we import from the existing auth service.
from ..auth.service import get_current_user
from .permissions import check_permissions

class RouterFactory:
    """
    Standardizes the creation of API endpoints for Resources.
    """

    @classmethod
    def create_router(cls, model_class: Type[Any]):
        """
        Generates a FastAPI APIRouter for the given Aras.Model.
        """
        router = APIRouter(
            prefix=f"/{model_class.__tablename__}",
            tags=[model_class.__title__ if hasattr(model_class, "__title__") else model_class.__tablename__]
        )

        # 1. Dynamic Pydantic Schema Generation
        fields = {}
        for column in model_class.__table__.columns:
            if column.name in ['id', 'created_at', 'updated_at', 'deleted_at']:
                continue
            
            # Simple Type Mapping
            python_type = str
            col_type = str(column.type).lower()
            if col_type.startswith('int'): python_type = int
            elif col_type.startswith('bool'): python_type = bool
            elif col_type.startswith('float') or col_type.startswith('decimal'): python_type = float
            
            fields[column.name] = (Optional[python_type] if column.nullable else python_type, ... if not column.nullable else None)

        # Inherit from Level 2 Validation
        from ..base.validation import Validation
        Schema = create_model(f"{model_class.__name__}Schema", __base__=Validation, **fields)

        # 2. Standard Endpoints
        
        @router.get("/metadata", response_model=dict)
        async def get_metadata():
            """Returns metadata for dynamic GUI generation."""
            return model_class.get_ui_metadata()

        @router.get("/", response_model=List[dict])
        async def list_items(db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
            """Lists all records for this resource."""
            items = model_class.fetch(db)
            return [row.to_dict() for row in items]

        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_item(
            data: Schema, 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
        ):
            """Creates a new record with audit tracking."""
            item_data = data.dict()
            new_item = model_class().save(db, item_data, user_id=user.id, is_new=True)
            return new_item.to_dict()

        @router.get("/{item_id}")
        async def get_item(item_id: int, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
            """Fetches a single record by ID."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return item.to_dict()

        @router.put("/{item_id}")
        async def update_item(
            item_id: int, 
            data: Schema, 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
        ):
            """Updates an existing record with audit tracking."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            item_data = data.dict(exclude_unset=True)
            item.save(db, item_data, user_id=user.id, is_new=False)
            return item.to_dict()

        @router.delete("/{item_id}")
        async def delete_item(
            item_id: int, 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=True))
        ):
            """Deletes or soft-deletes a record."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            if hasattr(item, "delete_self"):
                item.delete_self(db, user_id=user.id)
            else:
                db.delete(item)
                db.commit()
            return {"message": "Deleted successfully"}

        # 3. Dynamic Master-Detail (Relation) Routes
        cls._attach_relation_routes(router, model_class)

        return router

    @classmethod
    def _attach_relation_routes(cls, router: APIRouter, model_class: Type[Any]):
        """
        Scans the model for relationships and attaches sub-resource routes.
        Example: /invoice/{id}/items
        """
        from sqlalchemy.orm import RelationshipProperty
        
        for prop in model_class.__mapper__.iterate_properties:
            if isinstance(prop, RelationshipProperty):
                rel_name = prop.key
                child_model = prop.mapper.class_
                
                # We need a separate function scope to capture rel_name and child_model
                def make_rel_route(r_name, c_model):
                    @router.get(f"/{{item_id}}/{r_name}", tags=[f"{model_class.__name__} Relations"])
                    async def list_relation_items(
                        item_id: int, 
                        db: Session = Depends(get_db), 
                        user: Any = Depends(get_current_user)
                    ):
                        parent = model_class.get(db, item_id)
                        if not parent:
                            raise HTTPException(status_code=404, detail="Parent not found")
                        
                        related_data = getattr(parent, r_name)
                        if isinstance(related_data, list):
                            return [item.to_dict() for item in related_data]
                        return related_data.to_dict() if related_data else None
                    
                make_rel_route(rel_name, child_model)
