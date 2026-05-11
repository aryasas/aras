from run import app
from arasCore.admin.menu_service import build_sidebar_menu
import json

with app.app_context():
    menu = build_sidebar_menu()
    print(json.dumps(menu, indent=2))
