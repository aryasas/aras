# -*- coding: utf-8 -*-
"""
arasCore/utils.py
General utilities — merged from lib/utils.py + lib/jinja.py
"""
import os
import sys
import inspect
import json
from datetime import datetime
from flask import request
from itertools import chain
from functools import wraps


# ── Color helpers ─────────────────────────────────────────────────────────────

class CommandColor:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

def print_mode(enable=None):
    pass


# ── Utilities class ───────────────────────────────────────────────────────────

class Utilities:

    @staticmethod
    def print_param(label, value):
        print(f"{CommandColor.OKBLUE}{label}{CommandColor.ENDC}{value}")

    @staticmethod
    def get_folder(prefix, *exclude):
        """
        Scan package dir for subfolders matching prefix, excluding listed names.
        Used by blueprint_loader to auto-discover app_* blueprints.
        """
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pkg  = os.path.join(base, "aras")  # still scanning old aras/ for now
        folders = [
            name for name in os.listdir(pkg)
            if os.path.isdir(os.path.join(pkg, name))
            and name.startswith(prefix)
            and name not in exclude
        ]
        return sorted(folders)

    @staticmethod
    def get_all_subclasses(cls):
        return cls.__subclasses__() + [
            g for s in cls.__subclasses__()
            for g in Utilities.get_all_subclasses(s)
        ]

    @staticmethod
    def get_subclasses(cls):
        return cls.__subclasses__()

    @staticmethod
    def get_classes():
        return inspect.getmembers(sys.modules[__name__], inspect.isclass)

    @staticmethod
    def get_classes_name():
        return [c[0] for c in Utilities.get_classes()]

    @staticmethod
    def get_classes_to_register(__name__, inc=None, exc=None):
        classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        if inc:
            classes = [c for c in classes if c[0] in inc]
        if exc:
            classes = [c for c in classes if c[0] not in exc]
        return classes

    @staticmethod
    def get_module(_class):
        return inspect.getmodule(_class)

    @staticmethod
    def get_function(__name__):
        return inspect.getmembers(sys.modules[__name__], inspect.isfunction)

    @staticmethod
    def print_request_info(param1, param2=None):
        print(f"[Request] {request.method} {request.url}")


# ── Logging ───────────────────────────────────────────────────────────────────

def configure_logging(app):
    """Setup logging from file config if LOGGING_CONFIG is set."""
    import logging
    from logging.config import fileConfig
    try:
        log_path = app.config.get("LOGGING_CONFIG")
        if log_path:
            os.makedirs(app.config.get("LOGGING_FOLDER", "log"), exist_ok=True)
            fileConfig(log_path)
            logging.getLogger("faker").setLevel(logging.ERROR)
    except Exception:
        pass


# ── Jinja helpers ─────────────────────────────────────────────────────────────

def set_jinja_env(app):
    """Register custom Jinja2 globals and filters."""
    app.jinja_env.add_extension("jinja2.ext.do")

    @app.template_filter('datetime')
    def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
        if isinstance(value, datetime):
            return value.strftime(fmt)
        return value

    @app.template_filter('tojson_pretty')
    def tojson_pretty(value):
        return json.dumps(value, indent=2, default=str)

    app.jinja_env.globals.update(
        now=datetime.utcnow,
        enumerate=enumerate,
        zip=zip,
        len=len,
    )
