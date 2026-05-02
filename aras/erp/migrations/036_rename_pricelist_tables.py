"""
Migration 036 — Rename pricelist tables:
  stock_price_list (old header)  → stock_price_type
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
        # ── Step 1: rename old header table to stock_price_type ────────────
        conn.execute(text(
            "ALTER TABLE stock_price_list RENAME TO stock_price_type"
        ))
        # Drop columns that moved to the rule table (price_type enum, valid_from, valid_to)
        for col in ("price_type", "valid_from", "valid_to"):
            try:
                conn.execute(text(f"ALTER TABLE stock_price_type DROP COLUMN {col}"))
            except Exception:
                pass
        # Rename unique constraint
        try:
            conn.execute(text(
                "ALTER TABLE stock_price_type "
                "RENAME INDEX uq_price_list_company_name TO uq_price_type_company_name"
            ))
        except Exception:
            pass

        # ── Step 2: rename rule table to stock_price_list ──────────────────
        conn.execute(text(
            "ALTER TABLE stock_product_price RENAME TO stock_price_list"
        ))
        # Rename price_list_id → price_type_id
        conn.execute(text(
            "ALTER TABLE stock_price_list "
            "CHANGE price_list_id price_type_id INT NULL"
        ))
        # Update FK to point to new stock_price_type
        try:
            conn.execute(text(
                "ALTER TABLE stock_price_list DROP FOREIGN KEY stock_product_price_ibfk_price_list"
            ))
        except Exception:
            pass
        # Add correct FK
        try:
            conn.execute(text(
                "ALTER TABLE stock_price_list "
                "ADD CONSTRAINT fk_price_list_price_type "
                "FOREIGN KEY (price_type_id) REFERENCES stock_price_type(id)"
            ))
        except Exception:
            pass

        # ── Step 3: retarget FK columns in other tables ────────────────────
        # terminal: selling_pricelist_id, purchase_pricelist_id
        for fk_name in (
            "uq_pos_terminal_code",  # placeholder — drop old FK by col
        ):
            pass
        for tbl, col in [
            ("pos_terminal",        "selling_pricelist_id"),
            ("pos_terminal",        "purchase_pricelist_id"),
            ("acc_sales_invoice",   "price_type_id"),
            ("acc_purchase_invoice","price_type_id"),
            ("acc_sales_order",     "price_type_id"),
            ("sup_purchase_order",  "price_type_id"),
        ]:
            # Drop old FK constraint (ignore errors — constraint name varies)
            try:
                result = conn.execute(text(
                    f"SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                    f"WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{tbl}' "
                    f"AND COLUMN_NAME='{col}' AND REFERENCED_TABLE_NAME IS NOT NULL"
                ))
                for row in result:
                    try:
                        conn.execute(text(f"ALTER TABLE {tbl} DROP FOREIGN KEY `{row[0]}`"))
                    except Exception:
                        pass
            except Exception:
                pass
            # For non-terminal tables: rename price_list_id → price_type_id if not done
            if col == "price_type_id":
                try:
                    conn.execute(text(
                        f"ALTER TABLE {tbl} CHANGE price_list_id price_type_id INT NULL"
                    ))
                except Exception:
                    pass
            # Add new FK pointing to stock_price_type
            try:
                conn.execute(text(
                    f"ALTER TABLE {tbl} "
                    f"ADD CONSTRAINT fk_{tbl}_{col}_price_type "
                    f"FOREIGN KEY ({col}) REFERENCES stock_price_type(id)"
                ))
            except Exception:
                pass

        # promo_bundle: price_list_id → price_type_id
        try:
            conn.execute(text(
                "ALTER TABLE stock_promo_bundle CHANGE price_list_id price_type_id INT NULL"
            ))
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
