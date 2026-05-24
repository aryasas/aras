"""
Seed naming series for all ERP document types from seeds/series.yaml.
Run: cd api && python apps/erp/config/seed_series.py
"""
import sys
import yaml
from pathlib import Path

sys.path.insert(0, ".")

from core.registry.series import Series

SEED_FILE = Path(__file__).parent.parent / "seeds" / "series.yaml"


def run(db=None):
    """Seed series. Pass db to reuse an existing session, or omit to open one."""
    data = yaml.safe_load(SEED_FILE.read_text())
    own_session = db is None
    if own_session:
        from core.lib.database import SessionLocal
        db = SessionLocal()
    try:
        for s in data["series"]:
            existing = db.query(Series).filter_by(key=s["key"]).first()
            if existing:
                print(f"[SKIP] {s['key']}")
                continue
            db.add(Series(
                key=s["key"],
                prefix=s["prefix"],
                format=s["format"],
                next_value=1,
                config=s.get("config", {}),
            ))
            print(f"[OK]   {s['key']} → {s['prefix']}")
        if own_session:
            db.commit()
        else:
            db.flush()
    finally:
        if own_session:
            db.close()
    print("Done.")


if __name__ == "__main__":
    run()
