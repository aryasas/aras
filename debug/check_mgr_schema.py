import os
from sqlalchemy import inspect
from run import app
from arasCore.lib.core.extensions import db

with app.app_context():
    inspector = inspect(db.engine)
    print("mgr_table columns:")
    for col in inspector.get_columns('mgr_table'):
        print(col['name'])
    
    print("\nmgr_column columns:")
    for col in inspector.get_columns('mgr_column'):
        print(col['name'])
