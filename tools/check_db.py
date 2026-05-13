import sys
sys.path.append('./api')
from core.lib.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SHOW TABLES;"))
    tables = [row[0] for row in res]
    print("TABLES:", tables)
