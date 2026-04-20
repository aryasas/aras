"""Idempotent DB fixes for Task-4: add shift_number to pos_session, insert pos.shift sequence."""
from arasCore.lib.extensions import db
from sqlalchemy import text


def run(app):
    with app.app_context():
        _add_shift_number_column()
        _insert_pos_shift_sequence()
        print("[migrate_task4] done.")


def _add_shift_number_column():
    engine = db.engine
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() "
            "AND table_name = 'pos_session' "
            "AND column_name = 'shift_number'"
        ))
        if result.scalar() == 0:
            conn.execute(text(
                "ALTER TABLE pos_session ADD COLUMN shift_number VARCHAR(30) NULL"
            ))
            conn.commit()
            print("[migrate_task4] pos_session.shift_number added.")
        else:
            print("[migrate_task4] pos_session.shift_number already exists.")


def _insert_pos_shift_sequence():
    engine = db.engine
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM core_sequence WHERE code = 'pos.shift'"
        ))
        if result.scalar() == 0:
            company = conn.execute(text(
                "SELECT id FROM core_company WHERE code = 'HQ' LIMIT 1"
            )).fetchone()
            if company:
                conn.execute(text(
                    "INSERT INTO core_sequence (company_id, code, prefix, padding, reset_period, next_value) "
                    "VALUES (:cid, 'pos.shift', 'SHIFT', 5, 'yearly', 0)"
                ), {"cid": company[0]})
                conn.commit()
                print("[migrate_task4] pos.shift sequence inserted.")
        else:
            print("[migrate_task4] pos.shift sequence already exists.")
