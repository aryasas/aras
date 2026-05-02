"""Migration 035 — Promo scope columns on stock_product_price + promo bundle tables."""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn  = db.engine.connect()
    trans = conn.begin()
    try:
        # 1. Make product_id nullable on stock_product_price
        conn.execute(db.text(
            "ALTER TABLE stock_product_price MODIFY COLUMN product_id INT NULL"
        ))

        # 2. Add scope + discount columns
        for col_def in [
            "ADD COLUMN IF NOT EXISTS product_category_id INT NULL",
            "ADD COLUMN IF NOT EXISTS location_id         INT NULL",
            "ADD COLUMN IF NOT EXISTS terminal_id         INT NULL",
            "ADD COLUMN IF NOT EXISTS is_blanket          TINYINT(1) NOT NULL DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS discount_pct        DECIMAL(5,2) NULL",
        ]:
            conn.execute(db.text(f"ALTER TABLE stock_product_price {col_def}"))

        # 3. FK constraints
        fk_defs = [
            ("fk_spp_category", "product_category_id", "stock_product_category", "id"),
            ("fk_spp_location",  "location_id",         "stock_location",         "id"),
            ("fk_spp_terminal",  "terminal_id",          "pos_terminal",           "id"),
        ]
        for name, col, ref_table, ref_col in fk_defs:
            exists = conn.execute(db.text(
                "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_product_price' "
                f"AND CONSTRAINT_NAME = '{name}'"
            )).scalar()
            if not exists:
                conn.execute(db.text(
                    f"ALTER TABLE stock_product_price ADD CONSTRAINT {name} "
                    f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col}) ON DELETE SET NULL"
                ))

        # 4. Performance index
        idx_exists = conn.execute(db.text(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_product_price' "
            "AND INDEX_NAME = 'idx_spp_scope'"
        )).scalar()
        if not idx_exists:
            conn.execute(db.text(
                "CREATE INDEX idx_spp_scope ON stock_product_price "
                "(price_list_id, is_active, is_blanket, product_id, product_category_id)"
            ))

        # 5. Create stock_promo_bundle
        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS stock_promo_bundle (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                price_list_id INT NULL,
                name          VARCHAR(100) NOT NULL,
                valid_from    DATE NULL,
                valid_to      DATE NULL,
                is_active     TINYINT(1) NOT NULL DEFAULT 1,
                notes         TEXT NULL,
                created_at    DATETIME NULL,
                updated_at    DATETIME NULL,
                CONSTRAINT fk_spb_pricelist FOREIGN KEY (price_list_id)
                    REFERENCES stock_price_list(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # 6. Create stock_promo_bundle_item
        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS stock_promo_bundle_item (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                promo_bundle_id INT NOT NULL,
                product_id      INT NOT NULL,
                qty             DECIMAL(12,4) NOT NULL DEFAULT 1,
                uom_id          INT NULL,
                promo_price     DECIMAL(18,4) NULL,
                discount_pct    DECIMAL(5,2) NULL,
                created_at      DATETIME NULL,
                updated_at      DATETIME NULL,
                CONSTRAINT fk_spbi_bundle  FOREIGN KEY (promo_bundle_id)
                    REFERENCES stock_promo_bundle(id) ON DELETE CASCADE,
                CONSTRAINT fk_spbi_product FOREIGN KEY (product_id)
                    REFERENCES stock_product(id) ON DELETE CASCADE,
                CONSTRAINT fk_spbi_uom     FOREIGN KEY (uom_id)
                    REFERENCES stock_uom(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
