"""
Migration 026 — Payment refactor + Sales/Purchase Order + Delivery

Changes:
- Create acc_payment + acc_payment_allocation (replaces acc_invoice_payment)
- Create acc_sales_order + lines + charges
- Create sup_purchase_order + lines + charges
- Create stk_delivery_trip + stk_delivery_order + stk_delivery_order_line
- Add origin_order_id to acc_sales_invoice and acc_purchase_invoice
- Drop vendor_name, vendor_ref from acc_purchase_invoice
- Migrate existing acc_invoice_payment rows → acc_payment + acc_payment_allocation
- Drop acc_invoice_payment
"""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        _create_tables(conn)
        _alter_invoice_tables(conn)
        _migrate_invoice_payments(conn)
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()


def _create_tables(conn):
    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS acc_payment (
            id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id          INT NOT NULL,
            name                VARCHAR(50) NOT NULL,
            payment_type        ENUM('inbound','outbound') NOT NULL,
            partner_type        ENUM('customer','supplier','other') NOT NULL DEFAULT 'customer',
            partner_id          BIGINT,
            payment_date        DATE NOT NULL,
            method              VARCHAR(50) NOT NULL DEFAULT 'cash',
            mode_of_payment_id  INT,
            total_amount        DECIMAL(18,4) NOT NULL,
            allocated_amount    DECIMAL(18,4) NOT NULL DEFAULT 0,
            state               ENUM('draft','posted','cancelled') NOT NULL DEFAULT 'draft',
            reference           VARCHAR(100),
            notes               TEXT,
            journal_entry_id    BIGINT,
            is_active           TINYINT(1) NOT NULL DEFAULT 1,
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id       INT,
            updated_by_id       INT,
            INDEX ix_acc_pay_company_date (company_id, payment_date),
            INDEX ix_acc_pay_partner (partner_type, partner_id)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS acc_payment_allocation (
            id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
            payment_id          BIGINT NOT NULL,
            sales_invoice_id    BIGINT,
            purchase_invoice_id BIGINT,
            amount              DECIMAL(18,4) NOT NULL,
            notes               VARCHAR(255),
            is_active           TINYINT(1) NOT NULL DEFAULT 1,
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id       INT,
            updated_by_id       INT,
            INDEX ix_acc_palloc_payment (payment_id),
            INDEX ix_acc_palloc_sinv (sales_invoice_id),
            INDEX ix_acc_palloc_pinv (purchase_invoice_id)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS acc_sales_order (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id      INT NOT NULL,
            name            VARCHAR(50) NOT NULL,
            customer_id     INT,
            location_id     INT,
            order_date      DATE NOT NULL,
            expected_date   DATE,
            currency_id     INT NOT NULL,
            price_list_id   INT,
            subtotal        DECIMAL(18,4) NOT NULL DEFAULT 0,
            discount_amt    DECIMAL(18,4) NOT NULL DEFAULT 0,
            charge_amt      DECIMAL(18,4) NOT NULL DEFAULT 0,
            total           DECIMAL(18,4) NOT NULL DEFAULT 0,
            state           ENUM('draft','confirmed','partial','closed','cancelled') NOT NULL DEFAULT 'draft',
            reference       VARCHAR(100),
            notes           TEXT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT,
            INDEX ix_so_company_date (company_id, order_date),
            INDEX ix_so_customer (customer_id),
            INDEX ix_so_state (state)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS acc_sales_order_line (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id        BIGINT NOT NULL,
            sequence        INT DEFAULT 0,
            product_id      INT,
            description     VARCHAR(255) NOT NULL,
            qty             DECIMAL(12,4) NOT NULL DEFAULT 1,
            qty_invoiced    DECIMAL(12,4) NOT NULL DEFAULT 0,
            uom_id          INT,
            unit_price      DECIMAL(18,4) NOT NULL DEFAULT 0,
            discount_pct    DECIMAL(5,2) NOT NULL DEFAULT 0,
            subtotal        DECIMAL(18,4) NOT NULL DEFAULT 0,
            account_id      BIGINT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS acc_sales_order_charge (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id        BIGINT NOT NULL,
            charge_id       INT NOT NULL,
            sequence        INT DEFAULT 10,
            base_amt        DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount          DECIMAL(18,4) NOT NULL DEFAULT 0,
            account_id      BIGINT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS sup_purchase_order (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id      INT NOT NULL,
            name            VARCHAR(50) NOT NULL,
            supplier_id     INT,
            location_id     INT,
            order_date      DATE NOT NULL,
            expected_date   DATE,
            currency_id     INT NOT NULL,
            price_list_id   INT,
            subtotal        DECIMAL(18,4) NOT NULL DEFAULT 0,
            discount_amt    DECIMAL(18,4) NOT NULL DEFAULT 0,
            charge_amt      DECIMAL(18,4) NOT NULL DEFAULT 0,
            total           DECIMAL(18,4) NOT NULL DEFAULT 0,
            state           ENUM('draft','confirmed','partial','closed','cancelled') NOT NULL DEFAULT 'draft',
            reference       VARCHAR(100),
            notes           TEXT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT,
            INDEX ix_po_company_date (company_id, order_date),
            INDEX ix_po_supplier (supplier_id),
            INDEX ix_po_state (state)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS sup_purchase_order_line (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id        BIGINT NOT NULL,
            sequence        INT DEFAULT 0,
            product_id      INT,
            description     VARCHAR(255) NOT NULL,
            qty             DECIMAL(12,4) NOT NULL DEFAULT 1,
            qty_received    DECIMAL(12,4) NOT NULL DEFAULT 0,
            uom_id          INT,
            unit_price      DECIMAL(18,4) NOT NULL DEFAULT 0,
            discount_pct    DECIMAL(5,2) NOT NULL DEFAULT 0,
            subtotal        DECIMAL(18,4) NOT NULL DEFAULT 0,
            account_id      BIGINT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS sup_purchase_order_charge (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id        BIGINT NOT NULL,
            charge_id       INT NOT NULL,
            sequence        INT DEFAULT 10,
            base_amt        DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount          DECIMAL(18,4) NOT NULL DEFAULT 0,
            account_id      BIGINT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS stk_delivery_trip (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id      INT NOT NULL,
            name            VARCHAR(50) NOT NULL,
            trip_date       DATE NOT NULL,
            driver_name     VARCHAR(200),
            vehicle_no      VARCHAR(50),
            state           ENUM('draft','in_progress','completed','cancelled') NOT NULL DEFAULT 'draft',
            notes           TEXT,
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT,
            INDEX ix_dtrip_company_date (company_id, trip_date)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS stk_delivery_order (
            id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id          INT NOT NULL,
            name                VARCHAR(50) NOT NULL,
            sales_invoice_id    BIGINT,
            sales_order_id      BIGINT,
            customer_id         INT,
            src_location_id     INT,
            delivery_date       DATE,
            state               ENUM('draft','assigned','in_transit','delivered','cancelled') NOT NULL DEFAULT 'draft',
            notes               TEXT,
            trip_id             BIGINT,
            is_active           TINYINT(1) NOT NULL DEFAULT 1,
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id       INT,
            updated_by_id       INT,
            INDEX ix_do_company_date (company_id, delivery_date),
            INDEX ix_do_state (state)
        )
    """))

    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS stk_delivery_order_line (
            id              BIGINT AUTO_INCREMENT PRIMARY KEY,
            delivery_id     BIGINT NOT NULL,
            product_id      INT,
            description     VARCHAR(255) NOT NULL,
            qty             DECIMAL(12,4) NOT NULL DEFAULT 1,
            uom_id          INT,
            notes           VARCHAR(255),
            is_active       TINYINT(1) NOT NULL DEFAULT 1,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by_id   INT,
            updated_by_id   INT
        )
    """))


def _alter_invoice_tables(conn):
    # add origin_order_id to sales invoice
    try:
        conn.execute(db.text(
            "ALTER TABLE acc_sales_invoice ADD COLUMN origin_order_id BIGINT"
        ))
    except Exception:
        pass  # column already exists

    # add origin_order_id to purchase invoice
    try:
        conn.execute(db.text(
            "ALTER TABLE acc_purchase_invoice ADD COLUMN origin_order_id BIGINT"
        ))
    except Exception:
        pass

    # drop vendor_name from purchase invoice (data already in supplier_id)
    try:
        conn.execute(db.text(
            "ALTER TABLE acc_purchase_invoice DROP COLUMN vendor_name"
        ))
    except Exception:
        pass

    # drop vendor_ref from purchase invoice
    try:
        conn.execute(db.text(
            "ALTER TABLE acc_purchase_invoice DROP COLUMN vendor_ref"
        ))
    except Exception:
        pass


def _migrate_invoice_payments(conn):
    """Migrate acc_invoice_payment rows → acc_payment + acc_payment_allocation."""
    result = conn.execute(db.text(
        "SELECT COUNT(*) as cnt FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = 'acc_invoice_payment'"
    )).fetchone()
    if not result or result[0] == 0:
        return

    rows = conn.execute(db.text(
        "SELECT id, sales_invoice_id, purchase_invoice_id, payment_date, "
        "       method, amount, reference, notes, journal_entry_id "
        "FROM acc_invoice_payment"
    )).fetchall()

    for row in rows:
        pay_type    = "inbound" if row.sales_invoice_id else "outbound"
        partner_type = "customer" if row.sales_invoice_id else "supplier"

        # get company_id from the linked invoice
        if row.sales_invoice_id:
            inv = conn.execute(db.text(
                "SELECT company_id, customer_id FROM acc_sales_invoice WHERE id = :id"
            ), {"id": row.sales_invoice_id}).fetchone()
            company_id = inv.company_id if inv else 1
            partner_id = inv.customer_id if inv else None
        else:
            inv = conn.execute(db.text(
                "SELECT company_id, supplier_id FROM acc_purchase_invoice WHERE id = :id"
            ), {"id": row.purchase_invoice_id}).fetchone()
            company_id = inv.company_id if inv else 1
            partner_id = inv.supplier_id if inv else None

        conn.execute(db.text("""
            INSERT INTO acc_payment
                (company_id, name, payment_type, partner_type, partner_id,
                 payment_date, method, total_amount, allocated_amount,
                 state, reference, notes, journal_entry_id)
            VALUES
                (:company_id, :name, :pay_type, :partner_type, :partner_id,
                 :payment_date, :method, :amount, :amount,
                 'posted', :reference, :notes, :journal_entry_id)
        """), {
            "company_id":       company_id,
            "name":             f"PAY-MIGR-{row.id:05d}",
            "pay_type":         pay_type,
            "partner_type":     partner_type,
            "partner_id":       partner_id,
            "payment_date":     row.payment_date,
            "method":           row.method,
            "amount":           row.amount,
            "reference":        row.reference,
            "notes":            row.notes,
            "journal_entry_id": row.journal_entry_id,
        })

        new_pay_id = conn.execute(db.text("SELECT LAST_INSERT_ID()")).scalar()

        conn.execute(db.text("""
            INSERT INTO acc_payment_allocation
                (payment_id, sales_invoice_id, purchase_invoice_id, amount)
            VALUES
                (:payment_id, :sales_invoice_id, :purchase_invoice_id, :amount)
        """), {
            "payment_id":          new_pay_id,
            "sales_invoice_id":    row.sales_invoice_id,
            "purchase_invoice_id": row.purchase_invoice_id,
            "amount":              row.amount,
        })

    conn.execute(db.text("DROP TABLE acc_invoice_payment"))
