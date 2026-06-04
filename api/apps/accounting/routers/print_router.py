from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from core import Aras
from core.lib.database import get_db
from core.logic.permissions import RBAC, check_permissions

router = APIRouter()

SUPPORTED_RESOURCES = {
    "accounting_inflow_invoices",
    "accounting_outflow_invoices",
    "accounting_grns",
}


@router.get("/accounting/{resource}/{id}/print")
def get_printable_document(
    resource: str,
    id: int,
    db: Session = Depends(get_db),
    user: object = Depends(check_permissions(resource=None)),
):
    if resource not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Unsupported resource: {resource}")

    model_class = Aras.Model.get_model(resource)
    if not user.is_admin and not RBAC.has_permission(db, user, model_class.__tablename__, "READ"):
        raise HTTPException(status_code=403, detail=f"No READ permission on {model_class.__tablename__}")

    record = db.query(model_class).filter(model_class.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    request_org_id = getattr(record, "org_id", None)
    if request_org_id and getattr(user, "is_admin", False) is False:
        from core.auth.service import user_can_access_org
        if not user_can_access_org(db, user, request_org_id):
            raise HTTPException(status_code=404, detail="Record not found")

    # Org name via registry
    org_name = ""
    org_id = getattr(record, "org_id", None)
    if org_id:
        Organization = Aras.Model.get_model("core_organizations")
        org = db.get(Organization, org_id)
        if org:
            org_name = getattr(org, "trade_name", None) or getattr(org, "name", "")

    # Party name via registry
    party_name = "N/A"
    party_id = getattr(record, "party_id", None)
    if party_id:
        Party = Aras.Model.get_model("party_parties")
        party = db.get(Party, party_id)
        if party:
            party_name = getattr(party, "name", "N/A")

    lines_data: List[Dict[str, Any]] = []
    for line in getattr(record, "lines", []):
        qty = float(getattr(line, "qty", 0) or 0)
        unit_price = float(getattr(line, "unit_price", 0) or 0)
        subtotal = float(getattr(line, "subtotal", qty * unit_price) or qty * unit_price)
        lines_data.append({
            "description": getattr(line, "description", None) or getattr(line, "name", ""),
            "qty": qty,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    charges_data: List[Dict[str, Any]] = []
    for charge in getattr(record, "charges", []):
        charges_data.append({
            "description": getattr(charge, "description", None) or getattr(charge, "name", ""),
            "amount": float(getattr(charge, "amount", 0) or 0),
        })

    subtotal = sum(l["subtotal"] for l in lines_data)
    total_charge = sum(c["amount"] for c in charges_data)
    doc_date = getattr(record, "doc_date", None)

    return {
        "doc_type": model_class.__name__,
        "doc_number": getattr(record, "number", None) or getattr(record, "name", str(record.id)),
        "date": doc_date.isoformat() if doc_date else None,
        "party_name": party_name,
        "lines": lines_data,
        "charges": charges_data,
        "subtotal": subtotal,
        "total_charge": total_charge,
        "total_amount": subtotal + total_charge,
        "org_name": org_name,
    }
