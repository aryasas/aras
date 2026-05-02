# -*- coding: utf-8 -*-
"""arasCore/context.py — Global context processors."""
from flask import g
from flask_login import current_user

def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        from arasCore.admin.models import ArasSystemSetting
        import json
        
        tokens_raw = ArasSystemSetting.get("core.theme_tokens", "{}")
        if isinstance(tokens_raw, str):
            try:
                tokens = json.loads(tokens_raw)
            except:
                tokens = {}
        else:
            tokens = tokens_raw
            
        return {
            "user":  current_user,
            "gmenu": getattr(g, "gmenu", []),
            "aras_theme_tokens": tokens
        }
