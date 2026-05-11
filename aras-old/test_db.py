from run import app
from arasCore.admin.models import AppManagerTable
with app.app_context():
    tables = AppManagerTable.query.filter_by(page_type="group").all()
    for t in tables:
        print(f"Group: {t.title} | url_suffix: '{t.url_suffix}'")
