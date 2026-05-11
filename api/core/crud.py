from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Type, Any, Optional
from pydantic import create_model, BaseModel

from .lib.database import get_db
from .auth.service import get_current_user
from .lib.permissions import check_permissions

def create_aras_router(model_class: Type[Any]):
    """
    Otomatis membuat APIRouter dengan standar CRUD untuk ArasModel apapun.
    """
    router = APIRouter(
        prefix=f"/{model_class.__tablename__}",
        tags=[model_class.__title__ if hasattr(model_class, "__title__") else model_class.__tablename__]
    )

    # Dynamic Pydantic Models for Validation
    fields = {}
    for column in model_class.__table__.columns:
        if column.name in ['id', 'created_at', 'updated_at']:
            continue
        # Simplistic mapping: String -> str, Integer -> int, etc.
        python_type = str
        if str(column.type).lower().startswith('int'): python_type = int
        if str(column.type).lower().startswith('bool'): python_type = bool
        if str(column.type).lower().startswith('float'): python_type = float
        
        fields[column.name] = (Optional[python_type] if column.nullable else python_type, ... if not column.nullable else None)

    Schema = create_model(f"{model_class.__name__}Schema", **fields)
    # Enable ORM mode for Pydantic v2
    Schema.model_config = {"from_attributes": True}

    @router.get("/metadata", response_model=dict)
    async def get_metadata():
        return model_class.get_ui_metadata()

    @router.get("/", response_model=List[dict])
    async def list_items(db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
        items = db.query(model_class).all()
        return [row.to_dict() for row in items]

    @router.post("/", status_code=status.HTTP_201_CREATED)
    async def create_item(
        data: Schema, 
        db: Session = Depends(get_db), 
        user: Any = Depends(get_current_user),
        _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
    ):
        item_data = data.dict()
        # Auto-assign created_by
        if hasattr(model_class, 'created_by'):
            item_data['created_by'] = user.id
            
        new_item = model_class(**item_data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item

    @router.get("/{item_id}")
    async def get_item(item_id: int, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    @router.put("/{item_id}")
    async def update_item(
        item_id: int, 
        data: Schema, 
        db: Session = Depends(get_db), 
        user: Any = Depends(get_current_user),
        _: Any = Depends(check_permissions(required_admin=getattr(model_class, "__admin_only__", False)))
    ):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item_data = data.dict(exclude_unset=True)
        # Auto-assign updated_by
        if hasattr(model_class, 'updated_by'):
            item_data['updated_by'] = user.id
            
        for key, value in item_data.items():
            setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}")
    async def delete_item(
        item_id: int, 
        db: Session = Depends(get_db), 
        user: Any = Depends(get_current_user),
        _: Any = Depends(check_permissions(required_admin=True))
    ):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db.delete(item)
        db.commit()
        return {"message": "Deleted successfully"}

    return router
