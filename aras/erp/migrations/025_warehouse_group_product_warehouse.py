"""025 — Merge StockWarehouse into StockLocation (single location hierarchy).
  - stock_location: add company_id, code, is_group; migrate warehouse data in
  - acc_sales_invoice: rename warehouse_id -> location_id
  - acc_purchase_invoice: rename warehouse_id -> location_id
  - pos_terminal: rename warehouse_id -> location_id
  - stock_product_location: new table (replaces stock_product_warehouse)
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.core.extensions import db

    with flask_app.app_context():
        insp = inspect(db.engine)
        tables = set(insp.get_table_names())

        # ── stock_location: add company_id, code, is_group ────────────────────
        loc_cols = {c["name"] for c in insp.get_columns("stock_location")}
        if "company_id" not in loc_cols:
            db.session.execute(text(
                "ALTER TABLE stock_location ADD COLUMN company_id INT NULL REFERENCES company(id)"
            ))
            logger.info("[025] stock_location.company_id added")
        if "code" not in loc_cols:
            db.session.execute(text(
                "ALTER TABLE stock_location ADD COLUMN code VARCHAR(20) NULL"
            ))
            logger.info("[025] stock_location.code added")
        if "is_group" not in loc_cols:
            db.session.execute(text(
                "ALTER TABLE stock_location ADD COLUMN is_group TINYINT(1) NOT NULL DEFAULT 0"
            ))
            logger.info("[025] stock_location.is_group added")
        if "is_active" not in loc_cols:
            db.session.execute(text(
                "ALTER TABLE stock_location ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"
            ))
            db.session.execute(text("UPDATE stock_location SET is_active=1"))
            logger.info("[025] stock_location.is_active added")

        # ── Migrate stock_warehouse rows into stock_location ──────────────────
        if "stock_warehouse" in tables:
            wh_cols = {c["name"] for c in insp.get_columns("stock_warehouse")}
            is_group_col = "is_group" in wh_cols
            parent_col   = "parent_id" in wh_cols
            wh_rows = db.session.execute(text("SELECT * FROM stock_warehouse")).fetchall()
            for wh in wh_rows:
                existing = db.session.execute(
                    text("SELECT id FROM stock_location WHERE company_id=:cid AND name=:n AND location_type='internal'"),
                    {"cid": wh.company_id, "n": wh.name}
                ).fetchone()
                if not existing:
                    db.session.execute(text(
                        "INSERT INTO stock_location (name, company_id, location_type, is_group, is_active, created_at)"
                        " VALUES (:name, :cid, 'internal', 1, 1, NOW())"
                    ), {"name": wh.name, "cid": wh.company_id})
            logger.info("[025] stock_warehouse rows migrated to stock_location")

            # Update child locations: set company_id from parent warehouse
            db.session.execute(text("""
                UPDATE stock_location sl
                JOIN stock_warehouse wh ON sl.warehouse_id = wh.id
                SET sl.company_id = wh.company_id
                WHERE sl.company_id IS NULL AND sl.warehouse_id IS NOT NULL
            """))

            # Point child locations to new parent stock_location rows
            db.session.execute(text("""
                UPDATE stock_location sl
                JOIN stock_warehouse wh ON sl.warehouse_id = wh.id
                JOIN stock_location sl2 ON sl2.company_id = wh.company_id
                    AND sl2.name = wh.name AND sl2.location_type = 'internal' AND sl2.is_group = 1
                SET sl.parent_id = sl2.id
                WHERE sl.warehouse_id IS NOT NULL AND sl.is_group = 0
            """))

        db.session.flush()

        # ── acc_sales_invoice: warehouse_id -> location_id ────────────────────
        sal_cols = {c["name"] for c in insp.get_columns("acc_sales_invoice")}
        if "warehouse_id" in sal_cols and "location_id" not in sal_cols:
            db.session.execute(text(
                "ALTER TABLE acc_sales_invoice CHANGE warehouse_id location_id INT NULL"
            ))
            logger.info("[025] acc_sales_invoice: warehouse_id -> location_id")

        # ── acc_purchase_invoice: warehouse_id -> location_id ─────────────────
        pur_cols = {c["name"] for c in insp.get_columns("acc_purchase_invoice")}
        if "warehouse_id" in pur_cols and "location_id" not in pur_cols:
            db.session.execute(text(
                "ALTER TABLE acc_purchase_invoice CHANGE warehouse_id location_id INT NULL"
            ))
            logger.info("[025] acc_purchase_invoice: warehouse_id -> location_id")

        # ── pos_terminal: warehouse_id -> location_id ─────────────────────────
        term_cols = {c["name"] for c in insp.get_columns("pos_terminal")}
        if "warehouse_id" in term_cols and "location_id" not in term_cols:
            db.session.execute(text(
                "ALTER TABLE pos_terminal CHANGE warehouse_id location_id INT NULL"
            ))
            logger.info("[025] pos_terminal: warehouse_id -> location_id")

        # ── stock_product_location (new) ──────────────────────────────────────
        if "stock_product_location" not in tables:
            db.session.execute(text("""
                CREATE TABLE stock_product_location (
                    id            BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    product_id    INT           NOT NULL,
                    location_id   INT           NOT NULL,
                    min_qty       DECIMAL(12,4) NOT NULL DEFAULT 0,
                    max_qty       DECIMAL(12,4) NOT NULL DEFAULT 0,
                    notes         VARCHAR(255),
                    is_active     TINYINT(1)    NOT NULL DEFAULT 1,
                    created_at    DATETIME,
                    updated_at    DATETIME,
                    created_by_id INT,
                    updated_by_id INT,
                    FOREIGN KEY (product_id)  REFERENCES stock_product(id),
                    FOREIGN KEY (location_id) REFERENCES stock_location(id)
                )
            """))
            logger.info("[025] stock_product_location created")

        db.session.commit()
        logger.info("[025] done")
