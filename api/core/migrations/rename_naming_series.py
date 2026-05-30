"""Rename aras_naming_series to doc_series. Run BEFORE manage.py sync."""
import sys
sys.path.insert(0, ".")
from core.lib.database import SessionLocal
from sqlalchemy import text

SQL = """
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'aras_naming_series')
  AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'core_series')
  THEN
    ALTER TABLE aras_naming_series RENAME TO doc_series;
    RAISE NOTICE 'Renamed aras_naming_series to doc_series';
  ELSE
    RAISE NOTICE 'No rename needed';
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
