import os
from sqlalchemy import text
from run import app
from arasCore.lib.core.extensions import db

with app.app_context():
    res = db.session.execute(text("SELECT id, db_table_name FROM mgr_table WHERE db_table_name='erp_mode_of_payment'")).fetchone()
    if res:
        table_id = res[0]
        cols = db.session.execute(text(f"SELECT id, name, label FROM mgr_column WHERE table_id={table_id}")).fetchall()
        print(f"Columns for erp_mode_of_payment:")
        for c in cols:
            print(c)
            if c[1] == 'payment_type_id':
                print("Found stale payment_type_id, deleting...")
                db.session.execute(text(f"DELETE FROM mgr_column WHERE id={c[0]}"))
                db.session.commit()
                print("Deleted.")
    else:
        print("Table erp_mode_of_payment not found in mgr_table")
