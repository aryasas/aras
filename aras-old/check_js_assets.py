import os
from flask import Flask, url_for

app = Flask(__name__, static_folder='static')
with app.test_request_context():
    try:
        path = url_for('static', filename='js/bootstrap.min.js')
        print(f"Bootstrap exists: {os.path.exists(os.path.join('static', 'js/bootstrap.min.js'))}")
        print(f"URL: {path}")
    except Exception as e:
        print(e)
