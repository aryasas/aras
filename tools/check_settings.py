import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'api'))

from core import Aras
from core.registry.sys_settings import ArasSetting

def check_settings():
    db = next(Aras.get_db())
    settings = db.query(ArasSetting).all()
    print(f"Total settings: {len(settings)}")
    for s in settings:
        print(f"ID: {s.id}, Key: {s.key}, Value: {s.value}")

if __name__ == "__main__":
    check_settings()
