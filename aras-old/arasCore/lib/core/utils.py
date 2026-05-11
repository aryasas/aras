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
from flask import request, session
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
        pkg  = os.path.join(base, "app")  # still scanning old aras/ for now
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


# ── Pluggable company-settings provider ──────────────────────────────────────
# Apps that own a "Company" model (e.g. ERP) register a callable that returns the
# active Company instance for the current session. Framework code reads optional
# fields off it without importing the app directly.

_company_provider = None


def set_company_settings_provider(fn):
    """Register a callable -> active Company-like object (or None).
    Signature: fn() -> object | None"""
    global _company_provider
    _company_provider = fn


def _company_setting(field):
    """Return getattr(provider(), field) or None. Silent on any failure."""
    if not _company_provider:
        return None
    try:
        obj = _company_provider()
        if obj is None:
            return None
        return getattr(obj, field, None)
    except Exception:
        return None


# ── Jinja helpers ─────────────────────────────────────────────────────────────

def get_date_format(app_slug=None):
    """
    Get date format following hierarchy:
    1. App override (mgr_app.date_format)
    2. Company default (cfg_company.date_format)
    3. Global Aras default (aras_system_setting 'core.date_format')
    4. Final fallback
    """
    from arasCore.admin.models import ArasSystemSetting, AppManagerApp
    from arasCore.lib.core.extensions import db
    fmt = None
    
    # 1. App Override
    if app_slug:
        slug = app_slug.strip("/").lower()
        app = AppManagerApp.query.filter(db.or_(
            db.func.lower(AppManagerApp.url) == slug,
            db.func.lower(AppManagerApp.url) == f"/{slug}"
        )).first()
        if app and app.date_format:
            fmt = app.date_format
    
    # 2. Company Default
    if not fmt:
        fmt = _company_setting("date_format") or fmt

    # 3. Global Default
    if not fmt:
        fmt = ArasSystemSetting.get("core.date_format", "YYYY-MM-DD")
    
    # Normalize DD/MM/YYYY to %d/%m/%Y for strftime
    norm = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
    norm = norm.replace("YY", "%y").replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
    return norm

def get_number_format(app_slug=None):
    """
    Get number format following hierarchy:
    1. App override (mgr_app.number_format)
    2. Company default (cfg_company.number_format)
    3. Global Aras default (aras_system_setting 'core.number_format')
    """
    from arasCore.admin.models import ArasSystemSetting, AppManagerApp
    from arasCore.lib.core.extensions import db
    fmt = None
    
    # 1. App Override
    if app_slug:
        slug = app_slug.strip("/").lower()
        app = AppManagerApp.query.filter(db.or_(
            db.func.lower(AppManagerApp.url) == slug,
            db.func.lower(AppManagerApp.url) == f"/{slug}"
        )).first()
        if app and app.number_format:
            fmt = app.number_format
            
    # 2. Company Default
    if not fmt:
        fmt = _company_setting("number_format") or fmt

    # 3. Global Default
    if not fmt:
        fmt = ArasSystemSetting.get("core.number_format", "#,###.##")
    
    # Robust detection:
    # If both , and . exist, the last one is the decimal separator.
    if "," in fmt and "." in fmt:
        if fmt.rfind(",") > fmt.rfind("."):
            return (".", ",")
        else:
            return (",", ".")
    
    # If only one exists, it depends on its position.
    # If it's towards the end (last 3 chars), it's likely a decimal separator.
    if "," in fmt:
        last_comma = fmt.rfind(",")
        if last_comma >= len(fmt) - 3:
            return ("", ",")
        return (",", ".")
    
    if "." in fmt:
        last_dot = fmt.rfind(".")
        if last_dot >= len(fmt) - 3:
            return ("", ".")
        return (".", ",")
        
    return (",", ".")

def get_decimal_precision(app_slug=None):
    """
    Get decimal precision following hierarchy:
    1. App override (mgr_app.decimal_precision)
    2. Company default (cfg_company.decimal_precision)
    3. Global Aras default (aras_system_setting 'core.decimal_precision')
    4. Final fallback (2)
    """
    from arasCore.admin.models import ArasSystemSetting, AppManagerApp
    from arasCore.lib.core.extensions import db
    prec = None
    
    # 1. App Override
    if app_slug:
        slug = app_slug.strip("/").lower()
        app = AppManagerApp.query.filter(db.or_(
            db.func.lower(AppManagerApp.url) == slug,
            db.func.lower(AppManagerApp.url) == f"/{slug}"
        )).first()
        if app and app.decimal_precision is not None:
            prec = app.decimal_precision
    
    # 2. Company Default
    if prec is None:
        v = _company_setting("decimal_precision")
        if v is not None:
            prec = v

    # 3. Global Default
    if prec is None:
        prec = ArasSystemSetting.get("core.decimal_precision")
    
    if prec is None or prec == "":
        return 2
        
    try:
        return int(prec)
    except (ValueError, TypeError):
        return 2

def format_number(value, app_slug=None, precision=None):
    if value is None: return ""
    try:
        val = float(value)
    except (ValueError, TypeError):
        return value
    
    if precision is None:
        precision = get_decimal_precision(app_slug)
    
    try:
        precision = int(precision)
    except (ValueError, TypeError):
        precision = 2
        
    thousands_sep, decimal_sep = get_number_format(app_slug)
    
    # Start with standard Python formatting (comma thousands, dot decimal)
    s = f"{val:,.{precision}f}"
    
    # If separators match standard, return as is
    if thousands_sep == "," and decimal_sep == ".":
        return s
        
    # Handle the common Indonesian swap (comma -> dot, dot -> comma)
    if thousands_sep == "." and decimal_sep == ",":
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
    # Generic replacement
    # First, handle decimal separator (it's always a dot in 's')
    # Use a temporary placeholder if thousands_sep is a dot
    temp_s = s.replace(".", "DEC_SEP")
    
    # Then handle thousands separator (it's always a comma in 's')
    if thousands_sep != ",":
        temp_s = temp_s.replace(",", thousands_sep)
    
    # Finally, put the correct decimal separator in
    return temp_s.replace("DEC_SEP", decimal_sep)

def parse_number(value, app_slug=None):
    if value is None or value == "": return None
    if isinstance(value, (int, float)): return value
    s = str(value).strip()
    if not s: return None
    
    thousands_sep, decimal_sep = get_number_format(app_slug)
    
    # Remove thousands separator
    if thousands_sep:
        s = s.replace(thousands_sep, "")
    
    # Replace decimal separator with dot
    if decimal_sep and decimal_sep != ".":
        s = s.replace(decimal_sep, ".")
        
    try:
        # Check if it's an integer or float
        if "." in s:
            return float(s)
        return int(s)
    except (ValueError, TypeError):
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

def set_jinja_env(app):
    """Register custom Jinja2 globals and filters."""
    app.jinja_env.add_extension("jinja2.ext.do")

    @app.template_filter('datetime')
    def format_datetime_filter(value, fmt=None, app_slug=None):
        if not value: return ""
        if not fmt:
            fmt = get_date_format(app_slug)
        if isinstance(value, datetime):
            return value.strftime(fmt)
        return value

    @app.template_filter('number')
    def format_number_filter(value, precision=None, app_slug=None):
        return format_number(value, app_slug=app_slug, precision=precision)

    @app.template_filter('tojson_pretty')
    def tojson_pretty(value):
        return json.dumps(value, indent=2, default=str)

    app.jinja_env.globals.update(
        now=datetime.utcnow,
        enumerate=enumerate,
        zip=zip,
        len=len,
        get_decimal_precision=get_decimal_precision,
        get_number_format=get_number_format,
        get_date_format=get_date_format
    )
