# -*- coding: utf-8 -*-
"""arasCore/context.py — Global context processors."""
from flask import g
from flask_login import current_user

def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        return {
            "user":  current_user,
            "gmenu": getattr(g, "gmenu", []),
        }
