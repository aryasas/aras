"""
Migration 028 — Fix missing DEFAULT on pos/payment_allocation columns

- acc_payment_allocation: created_at/updated_at/is_active had no DEFAULT in some installs
- pos_terminal: is_active/created_at had no DEFAULT
- pos_order: created_at/updated_at had no DEFAULT
- pos_order_line: is_active/created_at had no DEFAULT
- pos_payment: is_active/created_at had no DEFAULT
- pos_shift_entry: created_at had no DEFAULT
"""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        # Backfill NULLs before adding NOT NULL constraint
        backfills = [
            "UPDATE acc_payment_allocation SET is_active=1 WHERE is_active IS NULL",
            "UPDATE acc_payment_allocation SET created_at=NOW() WHERE created_at IS NULL",
            "UPDATE acc_payment_allocation SET updated_at=NOW() WHERE updated_at IS NULL",
            "UPDATE pos_terminal SET is_active=1 WHERE is_active IS NULL",
            "UPDATE pos_terminal SET created_at=NOW() WHERE created_at IS NULL",
            "UPDATE pos_order SET created_at=NOW() WHERE created_at IS NULL",
            "UPDATE pos_order SET updated_at=NOW() WHERE updated_at IS NULL",
            "UPDATE pos_order_line SET is_active=1 WHERE is_active IS NULL",
            "UPDATE pos_order_line SET created_at=NOW() WHERE created_at IS NULL",
            "UPDATE pos_payment SET is_active=1 WHERE is_active IS NULL",
            "UPDATE pos_payment SET created_at=NOW() WHERE created_at IS NULL",
            "UPDATE pos_shift_entry SET created_at=NOW() WHERE created_at IS NULL",
        ]
        for stmt in backfills:
            conn.execute(db.text(stmt))

        stmts = [
            # acc_payment_allocation
            "ALTER TABLE acc_payment_allocation MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            "ALTER TABLE acc_payment_allocation MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE acc_payment_allocation MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            # pos_terminal
            "ALTER TABLE pos_terminal MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            "ALTER TABLE pos_terminal MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            # pos_order
            "ALTER TABLE pos_order MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE pos_order MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            # pos_order_line
            "ALTER TABLE pos_order_line MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            "ALTER TABLE pos_order_line MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            # pos_payment
            "ALTER TABLE pos_payment MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            "ALTER TABLE pos_payment MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            # pos_shift_entry
            "ALTER TABLE pos_shift_entry MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        ]
        for stmt in stmts:
            conn.execute(db.text(stmt))
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
