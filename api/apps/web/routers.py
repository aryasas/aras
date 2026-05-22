from fastapi import APIRouter, Depends, HTTPException
from core.base.validation import Validation
from typing import Optional
from sqlalchemy.orm import Session
from core.lib.database import get_db
from .models import WebPage, WebMenuItem, SiteSetting, ContactSubmission

router = APIRouter(prefix="", tags=["Web"])

class ContactRequest(Validation):
    name: str
    email: str
    subject: Optional[str] = None
    message: str

@router.get("/pages/{slug}")
def get_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(WebPage).filter(WebPage.slug == slug, WebPage.is_published == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "content": page.content,
        "meta_title": page.meta_title,
        "meta_description": page.meta_description,
        "template": page.template
    }

@router.get("/menu/{location}")
def get_menu(location: str, db: Session = Depends(get_db)):
    if location == "both":
        items = db.query(WebMenuItem).filter(WebMenuItem.is_active == True, WebMenuItem.parent_id == None).order_by(WebMenuItem.sort_order).all()
    else:
        items = db.query(WebMenuItem).filter(
            WebMenuItem.is_active == True, 
            WebMenuItem.menu_location.in_([location, "both"]),
            WebMenuItem.parent_id == None
        ).order_by(WebMenuItem.sort_order).all()

    def build_tree(item):
        return {
            "id": item.id,
            "label": item.label,
            "url": item.url,
            "menu_location": item.menu_location,
            "sort_order": item.sort_order,
            "children": [build_tree(child) for child in item.children if child.is_active]
        }

    return [build_tree(item) for item in items]

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(SiteSetting).all()
    return {s.key: s.value for s in settings}

@router.post("/contact")
def submit_contact(data: ContactRequest, db: Session = Depends(get_db)):
    submission = ContactSubmission(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message
    )
    db.add(submission)
    db.commit()
    return {"success": True}
