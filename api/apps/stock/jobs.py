# gpt-5
from datetime import datetime, timezone
import logging
from typing import Optional

from sqlalchemy import func

from core.lib.config import ConfigService
from core import Aras

logger = logging.getLogger(__name__)


# gpt-5
def _notification_recipient(org) -> Optional[str]:
    return getattr(org, "email", None) or None


# gpt-5
def _send_email(db, recipient: str, subject: str, text: str, html: str) -> None:
    from apps.saas.services.email import get_transport

    get_transport(db=db).send(recipient, subject, text=text, html=html)


# gpt-5
def send_low_stock_digest() -> None:
    from core.workspace.models import Organization
    from .models import Item, ItemLocation
    from .services.stock import StockComputeService

    db = next(Aras.get_db())
    try:
        if not ConfigService.flag(db, "stock.reorder.enable_reorder_alerts", True):
            logger.info("Low-stock digest skipped: reorder alerts disabled")
            return

        orgs = db.query(Organization).all()
        for org in orgs:
            recipient = _notification_recipient(org)
            if not recipient:
                logger.warning("Skipping low-stock digest for org %s: no notification email", org.id)
                continue

            threshold_rows = (
                db.query(Item.id, Item.name, Item.code, func.max(ItemLocation.min_qty))
                .join(ItemLocation, ItemLocation.item_id == Item.id)
                .filter(Item.org_id == org.id, ItemLocation.min_qty > 0)
                .group_by(Item.id, Item.name, Item.code)
                .all()
            )

            low_items: list[dict] = []
            for item_id, name, code, min_qty in threshold_rows:
                qty_on_hand = StockComputeService.compute_qty(db, item_id)
                if qty_on_hand <= float(min_qty or 0):
                    low_items.append(
                        {
                            "name": name,
                            "code": code,
                            "qty_on_hand": qty_on_hand,
                            "min_qty": float(min_qty or 0),
                        }
                    )

            if not low_items:
                continue

            lines = [
                f"- {row['name']} ({row['code'] or '-'}) qty={row['qty_on_hand']:.2f} min={row['min_qty']:.2f}"
                for row in low_items
            ]
            subject = f"Low stock alert for {org.name}"
            generated_at = datetime.now(timezone.utc).isoformat()
            text = (
                f"Low-stock digest for {org.name}\n"
                f"Generated at: {generated_at}\n\n"
                + "\n".join(lines)
            )
            html = (
                f"<p>Low-stock digest for <strong>{org.name}</strong></p>"
                f"<p>Generated at: {generated_at}</p>"
                "<ul>"
                + "".join(
                    f"<li>{row['name']} ({row['code'] or '-'}) qty={row['qty_on_hand']:.2f} min={row['min_qty']:.2f}</li>"
                    for row in low_items
                )
                + "</ul>"
            )
            _send_email(db, recipient, subject, text, html)
    finally:
        db.close()
