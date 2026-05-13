import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'api'))
from core.lib.database import SessionLocal
from core.registry.sys_settings import ArasSetting

db = SessionLocal()
try:
    settings = db.query(ArasSetting).all()
    print("ID | Key | Value")
    print("---|---|---")
    for s in settings:
        print(f"{s.id} | {s.key} | {s.value}")
finally:
    db.close()
