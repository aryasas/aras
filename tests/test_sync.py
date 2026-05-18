import sys
sys.path.append('./api')
from core import Aras
from core.lib.database import SessionLocal

db = SessionLocal()
try:
    Aras.Manager.Sync.sync_all(db)
    print("SYNC SUCCESS")
except Exception as e:
    import traceback
    print("SYNC ERROR:", e)
    traceback.print_exc()
finally:
    db.close()
