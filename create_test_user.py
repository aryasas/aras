from app import create_app
from arasCore.lib.core.extensions import db
from arasCore.auth import User, create_user

app = create_app()
with app.app_context():
    username = "test_login"
    email = "test_login@example.com"
    password = "password123"
    
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
    
    create_user(username, email, password, is_admin=True)
    print(f"Created user '{username}' with password '{password}'")
