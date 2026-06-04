# claude-sonnet-4-6
"""Drop stale NOT NULL on party_parties.code — model declares nullable=True.

Schema drift: Party.code was made optional in the model but the DB column
kept its NOT NULL constraint, breaking any insert without an explicit code
(e.g. test fixtures, auto-generated parties). Idempotent.

Run: python -m core.migrations.sync_party_code_nullable
"""
import sys
sys.path.insert(0, ".")
from core.lib.database import SessionLocal
from sqlalchemy import text

SQL = """
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'party_parties' AND column_name = 'code'
      AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE party_parties ALTER COLUMN code DROP NOT NULL;
    RAISE NOTICE 'party_parties.code is now nullable';
  ELSE
    RAISE NOTICE 'No change needed';
  END IF;
END $$;
"""


def run():
    db = SessionLocal()
    try:
        db.execute(text(SQL))
        db.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run()
