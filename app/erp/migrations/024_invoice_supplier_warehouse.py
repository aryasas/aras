"""024 — add supplier_id + warehouse_id to purchase invoice; warehouse_id to sales invoice;
         merge stock_price_list_item into stock_product_price (add price_list_id column)
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.core.extensions import db

    with flask_app.app_context():
        insp = inspect(db.engine)

        # ── acc_purchase_invoice: supplier_id + warehouse_id ─────────────────
        pur_cols = {c["name"] for c in insp.get_columns("acc_purchase_invoice")}
        if "supplier_id" not in pur_cols:
            db.session.execute(text(
                "ALTER TABLE acc_purchase_invoice ADD COLUMN supplier_id INT NULL"
                " AFTER company_id"
            ))
            logger.info("[024] added supplier_id to acc_purchase_invoice")
        if "warehouse_id" not in pur_cols:
            db.session.execute(text(
                "ALTER TABLE acc_purchase_invoice ADD COLUMN warehouse_id INT NULL"
                " AFTER supplier_id"
            ))
            logger.info("[024] added warehouse_id to acc_purchase_invoice")

        # ── acc_sales_invoice: warehouse_id ───────────────────────────────────
        sal_cols = {c["name"] for c in insp.get_columns("acc_sales_invoice")}
        if "warehouse_id" not in sal_cols:
            db.session.execute(text(
                "ALTER TABLE acc_sales_invoice ADD COLUMN warehouse_id INT NULL"
                " AFTER customer_id"
            ))
            logger.info("[024] added warehouse_id to acc_sales_invoice")

        # ── stock_product_price: price_list_id ───────────────────────────────
        tables = insp.get_table_names()
        spp_table = "stock_price_list" if "stock_price_list" in tables else ("stock_product_price" if "stock_product_price" in tables else None)
        
        if spp_table:
            pp_cols = {c["name"] for c in insp.get_columns(spp_table)}
            if "price_list_id" not in pp_cols:
                db.session.execute(text(
                    f"ALTER TABLE {spp_table} ADD COLUMN price_list_id INT NULL"
                    " AFTER product_id"
                ))
                logger.info(f"[024] added price_list_id to {spp_table}")

        # ── migrate stock_price_list_item → stock_product_price ──────────────
        if "stock_price_list_item" in tables and spp_table:
            rows = db.session.execute(text(
                "SELECT price_list_id, product_id, uom_id, price, min_qty,"
                "       discount_pct, valid_from, valid_to FROM stock_price_list_item"
            )).fetchall()
            migrated = 0
            for r in rows:
                exists = db.session.execute(text(
                    f"SELECT id FROM {spp_table}"
                    " WHERE product_id=:pid AND price_list_id=:plid AND uom_id=:uid AND min_qty=:mq"
                ), {"pid": r[1], "plid": r[0], "uid": r[2], "mq": r[4]}).fetchone()
                if not exists:
                    # Note: We assume stock_price_list already exists if we're migrating into it or stock_product_price
                    db.session.execute(text(
                        f"INSERT INTO {spp_table}"
                        " (product_id, price_list_id, name, price_type, currency_id,"
                        "  uom_id, price, min_qty, valid_from, valid_to, is_active)"
                        " SELECT :pid, :plid, pl.name, pl.price_type, pl.currency_id,"
                        "        :uid, :price, :mq, :vf, :vt, 1"
                        " FROM stock_price_list pl WHERE pl.id=:plid"
                    ), {
                        "pid": r[1], "plid": r[0], "uid": r[2],
                        "price": r[3], "mq": r[4], "vf": r[6], "vt": r[7],
                    })
                    migrated += 1
            logger.info(f"[024] migrated {migrated} rows from stock_price_list_item into {spp_table}")
            db.session.execute(text("DROP TABLE stock_price_list_item"))
            logger.info("[024] dropped stock_price_list_item")

        db.session.commit()
        logger.info("[024] done")
