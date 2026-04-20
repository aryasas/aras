# -*- coding: utf-8 -*-
"""
run.py — Entry point for arasCore.
Usage:
    python run.py
    flask run  (uses FLASK_RUN_PORT=8080 from .env)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from arasCore import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_RUN_PORT", os.getenv("PORT", 8080)))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False,   # ← matikan reloader, hindari double process
        use_debugger=True,
    )
