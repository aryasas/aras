from app import create_app
from arasCore.lib.core.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # Check current column definition
        print("Checking auth_users.password_hash size...")
        res = conn.execute(text("SHOW COLUMNS FROM auth_users LIKE 'password_hash'"))
        for row in res:
            print(f"Current column info: {row}")
        
        # Alter the column
        print("Resizing password_hash to VARCHAR(256)...")
        conn.execute(text("ALTER TABLE auth_users MODIFY password_hash VARCHAR(256)"))
        conn.commit()
        print("Done.")
