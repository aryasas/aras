import os
from sqlalchemy import inspect
from run import app
from arasCore.lib.core.extensions import db

with app.app_context():
    inspector = inspect(db.engine)
    print("Physical columns for erp_mode_of_payment:")
    cols = inspector.get_columns('erp_mode_of_payment')
    for col in cols:
        print(f"{col['name']} - {col['type']}")
