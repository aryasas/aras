"""
Migration 036 — Rename pricelist tables:
  stock_price_list (old header)  → stock_price_type  (copy data, then drop)
  stock_product_price (rules)    → stock_price_list
  price_list_id FK column        → price_type_id on rule table
  FK refs in terminal/invoice/order tables retargeted to stock_price_type
"""
from sqlalchemy import text


def run(flask_app):
    with flask_app.app_context():
        up(flask_app)


def up(flask_app):
    from arasCore.lib.core.extensions import db
    conn = db.engine.connect()
    t = conn.begin()
    try:
        def _table_exists(name):
            r = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:n"
            ), {"n": name})
            return r.scalar() > 0

        def _column_exists(tbl, col):
            r = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:t AND COLUMN_NAME=:c"
            ), {"t": tbl, "c": col})
            return r.scalar() > 0

        # ── Step 1: migrate old header data into stock_price_type ──────────
        if _table_exists("stock_price_list"):
            # Copy existing header rows preserving IDs
            conn.execute(text("""
                INSERT IGNORE INTO stock_price_type
                    (id, company_id, name, currency_id, description, created_at, updated_at)
                SELECT id, company_id, name, currency_id, description, created_at, updated_at
                FROM stock_price_list
            """))
            # Drop old header table (FK refs will be retargeted below)
            # First drop FKs pointing to it
            fk_result = conn.execute(text("""
                SELECT TABLE_NAME, CONSTRAINT_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA=DATABASE()
                  AND REFERENCED_TABLE_NAME='stock_price_list'
            """))
            for row in fk_result.fetchall():
                try:
                    conn.execute(text(f"ALTER TABLE `{row[0]}` DROP FOREIGN KEY `{row[1]}`"))
                except Exception:
                    pass
            conn.execute(text("DROP TABLE stock_price_list"))

        # ── Step 2: rename rule table to stock_price_list ──────────────────
if _table_exists("stock_product_price"):
            conn.execute(text("ALTER TABLE stock_product_price RENAME TO stock_price_list"))

        # Rename price_list_id → price_type_id
        if _table_exists("stock_price_list") and _column_exists("stock_price_list", "price_list_id"):
            conn.execute(text(
                "ALTER TABLE stock_price_list CHANGE price_list_id price_type_id INT NULL"
            ))
            # Drop old FK
            try:
                fk_result = conn.execute(text("""
                    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='stock_price_list'
                      AND COLUMN_NAME='price_type_id' AND REFERENCED_TABLE_NAME IS NOT NULL
                """))
                for row in fk_result.fetchall():
                    try:
                        conn.execute(text(f"ALTER TABLE stock_price_list DROP FOREIGN KEY `{row[0]}`"))
                    except Exception:
                        pass
            except Exception:
                pass
            # Add new FK
            try:
                conn.execute(text(
                    "ALTER TABLE stock_price_list "
                    "ADD CONSTRAINT fk_price_list_price_type "
                    "FOREIGN KEY (price_type_id) REFERENCES stock_price_type(id)"
                ))
            except Exception:
                pass

        # ── Step 3: retarget FKs in external tables ────────────────────────
        for tbl, col, old_col in [
            ("pos_terminal",         "selling_pricelist_id",  None),
            ("pos_terminal",         "purchase_pricelist_id", None),
            ("acc_sales_invoice",    "price_type_id",         "price_list_id"),
            ("acc_purchase_invoice", "price_type_id",         "price_list_id"),
            ("acc_sales_order",      "price_type_id",         "price_list_id"),
            ("sup_purchase_order",   "price_type_id",         "price_list_id"),
        ]:
            if not _table_exists(tbl):
                continue
            # Rename column if needed
            if old_col and _column_exists(tbl, old_col):
                conn.execute(text(f"ALTER TABLE `{tbl}` CHANGE `{old_col}` `{col}` INT NULL"))
            # Drop existing FK on this column
            try:
                fk_result = conn.execute(text(f"""
                    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{tbl}'
                      AND COLUMN_NAME='{col}' AND REFERENCED_TABLE_NAME IS NOT NULL
                """))
                for row in fk_result.fetchall():
                    try:
                        conn.execute(text(f"ALTER TABLE `{tbl}` DROP FOREIGN KEY `{row[0]}`"))
                    except Exception:
                        pass
            except Exception:
                pass
            # Add new FK → stock_price_type
            try:
                conn.execute(text(
                    f"ALTER TABLE `{tbl}` "
                    f"ADD CONSTRAINT `fk_{tbl}_{col}_price_type` "
                    f"FOREIGN KEY (`{col}`) REFERENCES stock_price_type(id)"
                ))
            except Exception:
                pass

        # promo_bundle: price_list_id → price_type_id
        if _table_exists("stock_promo_bundle") and _column_exists("stock_promo_bundle", "price_list_id"):
            conn.execute(text(
                "ALTER TABLE stock_promo_bundle CHANGE price_list_id price_type_id INT NULL"
            ))
        if _table_exists("stock_promo_bundle"):
            try:
                fk_result = conn.execute(text("""
                    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='stock_promo_bundle'
                      AND COLUMN_NAME='price_type_id' AND REFERENCED_TABLE_NAME IS NOT NULL
                """))
                for row in fk_result.fetchall():
                    try:
                        conn.execute(text(f"ALTER TABLE stock_promo_bundle DROP FOREIGN KEY `{row[0]}`"))
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                conn.execute(text(
                    "ALTER TABLE stock_promo_bundle "
                    "ADD CONSTRAINT fk_promo_bundle_price_type "
                    "FOREIGN KEY (price_type_id) REFERENCES stock_price_type(id)"
                ))
            except Exception:
                pass

        t.commit()
        print("036: rename complete")
    except Exception as e:
        t.rollback()
        raise RuntimeError(f"036 migration failed: {e}") from e
    finally:
        conn.close()
