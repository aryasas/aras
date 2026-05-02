
from run import app
from flask import url_for, request

with app.test_request_context('/admin/dev'):
    try:
        print(f"Endpoint: {request.endpoint}")
        # Try to build the problematic URL
        url = url_for('admin.dev_cli')
        print(f"Successfully built URL for admin.dev_cli: {url}")
    except Exception as e:
        print(f"Failed to build URL for admin.dev_cli: {e}")

with app.test_request_context('/admin/dev'):
    from flask import render_template
    try:
        # Simulate the template rendering
        # Note: we need to mock 'routes' and 'modules' because they are passed in the real view
        html = render_template('admin/setting/setting_dev_standalone.html', routes=[], modules=[], main_title="Test")
        print("Successfully rendered setting_dev_standalone.html")
    except Exception as e:
        print(f"Failed to render setting_dev_standalone.html: {e}")
