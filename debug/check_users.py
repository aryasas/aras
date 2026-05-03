from app import create_app
from arasCore.lib.core.extensions import db
from arasCore.auth import User

app = create_app()
with app.app_context():
    users = User.query.all()
    if not users:
        print("No users found in the database.")
    else:
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"- Username: {u.username}, Email: {u.email}, Is Admin: {u.is_admin}, Is Active: {u.is_active}")
