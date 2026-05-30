"""
Seed naming series for all ERP document types from seeds/series.yaml.
Run: cd api && python apps/config/seed_series.py
"""
import sys
import yaml
from pathlib import Path

sys.path.insert(0, ".")

from core.registry.series import Series

SEED_FILE = Path(__file__).parent.parent / "seeds" / "series.yaml"
from core.lib.config import config


def run(db=None):
    """Seed series. Pass db to reuse an existing session, or omit to open one."""
    data = yaml.safe_load(SEED_FILE.read_text())
    own_session = db is None
    if own_session:
        from core.lib.database import SessionLocal
        db = SessionLocal()
    try:
        for s in data["series"]:
            key = s["key"]
            fmt = s["format"]
            # Convert old format tokens to new ones
            # {prefix}, {year}, {next_value:04d} -> {prefix}, {year}, {seq:4}
            new_fmt = fmt.replace("{next_value:04d}", "{seq:4}").replace("{next_value:05d}", "{seq:5}").replace("{next_value}", "{seq}")

            config.set(db, f"core_config.numbering.{key}", new_fmt)
            print(f"[OK]   {key} → {new_fmt}")

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
