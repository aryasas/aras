import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Type, Any, Optional
from pydantic import create_model

from .database import get_db
from ..auth.service import get_current_user
from .permissions import check_permissions

class RouterFactory:
    """
    Generic factory for generating standardized CRUD routes for any Aras Model.
    Supports Enterprise features: Pagination, Advanced Filtering, Global Search, and Bulk Actions.
    """

    @classmethod
    def create_router(cls, model_class: Type[Any]):
        """
        Generates a FastAPI APIRouter for the given Aras.Model.
        """
        router = APIRouter(
            prefix=f"/{model_class.__tablename__}",
            tags=[getattr(model_class, "__title__", model_class.__tablename__)]
        )

        # ── 1. Dynamic Pydantic Schema Generation ─────────────────────────────
        fields = {}
        for column in model_class.__table__.columns:
            if column.name in ['id', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by']:
                continue
            
            python_type = Any
            try:
                python_type = column.type.python_type
            except:
                python_type = str
            
            default_val = ... if not column.nullable else None
            fields[column.name] = (Optional[python_type] if column.nullable else python_type, default_val)

        from ..base.validation import Validation
        Schema = create_model(f"{model_class.__name__}Schema", __base__=Validation, **fields)
        Schema.model_config = {"from_attributes": True}

        # ── 2. Standard Endpoints ─────────────────────────────────────────────
        
        @router.get("/metadata", response_model=dict)
        async def get_metadata(
            lang: Optional[str] = Query(None),
            db: Session = Depends(get_db)
        ):
            """Returns metadata for dynamic GUI generation with translation support."""
            translations = {}
            if lang:
                from ..aras import Aras
                # 1. Fetch Resource ID
                res = db.query(Aras.ResourceModel).filter(Aras.ResourceModel.name == model_class.__tablename__).first()
                if res:
                    # 2. Fetch Resource Translations
                    res_trans = db.query(Aras.TranslationModel).filter(
                        Aras.TranslationModel.registry_type == "resource",
                        Aras.TranslationModel.registry_id == res.id,
                        Aras.TranslationModel.language_code == lang
                    ).all()
                    for t in res_trans:
                        translations[f"resource.{t.property_name}"] = t.translated_value

                    # 3. Fetch Field Translations
                    # Join Translation with FieldModel to get translations for all fields of this resource
                    field_trans = db.query(Aras.TranslationModel, Aras.FieldModel.name).join(
                        Aras.FieldModel, Aras.FieldModel.id == Aras.TranslationModel.registry_id
                    ).filter(
                        Aras.TranslationModel.registry_type == "field",
                        Aras.FieldModel.resource_id == res.id,
                        Aras.TranslationModel.language_code == lang
                    ).all()
                    for t, field_name in field_trans:
                        translations[f"field.{field_name}.{t.property_name}"] = t.translated_value

            return model_class.get_ui_metadata(translations=translations)

        @router.get("/")
        async def list_items(
            page: int = Query(1, ge=1),
            per_page: int = Query(20, ge=1, le=100),
            search: Optional[str] = None,
            filters: Optional[str] = None,
            order_by: Optional[str] = None,
            desc: bool = True,
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user)
        ):
            """Lists records with pagination, filtering, and search."""
            parsed_filters = None
            if filters:
                try:
                    parsed_filters = json.loads(filters)
                except:
                    raise HTTPException(status_code=400, detail="Invalid filters format. Must be JSON.")
            
            return model_class.paginate(
                db, 
                page=page, 
                per_page=per_page, 
                search=search, 
                filters=parsed_filters,
                order_by=order_by, 
                desc=desc
            )

        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_item(
            data: Schema, 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
        ):
            """Creates a new record with hooks support."""
            new_item = model_class.create(db, data.dict(), user_id=user.id)
            return new_item.to_dict()

        @router.get("/{item_id}")
        async def get_item(item_id: int, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
            """Fetches a single record by ID."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

        @router.put("/{item_id}")
        async def update_item(
            item_id: int, 
            data: Schema, 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
        ):
            """Updates an existing record with hooks support."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            item.update_self(db, data.dict(exclude_unset=True), user_id=user.id)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

        @router.patch("/{item_id}")
        async def patch_item(
            item_id: int, 
            data: dict = Body(...), 
            db: Session = Depends(get_db), 
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
        ):
            """Partially updates an existing record."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            item.update_self(db, data, user_id=user.id)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

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
            
            item.delete_self(db, user_id=user.id)
            return {"message": "Deleted successfully", "id": item_id}

        @router.post("/bulk-delete")
        async def bulk_delete(
            ids: List[int],
            db: Session = Depends(get_db),
            user: Any = Depends(get_current_user),
            _: Any = Depends(check_permissions(required_admin=True))
        ):
            """Performs bulk deletion of multiple records."""
            deleted_count = 0
            for item_id in ids:
                item = model_class.get(db, item_id)
                if item:
                    item.delete_self(db, user_id=user.id)
                    deleted_count += 1
            return {"message": f"Successfully deleted {deleted_count} items", "deleted_count": deleted_count}

        return router
