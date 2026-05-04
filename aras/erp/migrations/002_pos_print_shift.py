"""002_pos_print_shift — add POS terminal print/shift fields and PosShiftEntry table."""
from arasCore.lib.core.extensions import db


def upgrade():
    conn = db.engine.connect()
    try:
        # PosTerminal new columns
        _add_column(conn, "pos_terminal", "invoice_sequence_id", "INTEGER REFERENCES sequence(id)")
        _add_column(conn, "pos_terminal", "print_template_id",   "INTEGER REFERENCES print_template(id)")
        _add_column(conn, "pos_terminal", "opening_journal_id",  "INTEGER REFERENCES acc_journal(id)")

        # PosShiftEntry table
        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS pos_shift_entry (
                id                BIGSERIAL PRIMARY KEY,
                session_id        INTEGER NOT NULL REFERENCES pos_session(id),
                entry_type        VARCHAR(20) NOT NULL,
                amount            NUMERIC(18,4) NOT NULL DEFAULT 0,
                note              VARCHAR(255),
                journal_entry_id  BIGINT REFERENCES acc_journal_entry(id),
                entered_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entered_by_id     INTEGER REFERENCES auth_users(id),
                is_active         BOOLEAN DEFAULT TRUE,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    finally:
        conn.close()


def _add_column(conn, table, col, definition):
    try:
        conn.execute(db.text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {definition}"))
    except Exception:
        pass
