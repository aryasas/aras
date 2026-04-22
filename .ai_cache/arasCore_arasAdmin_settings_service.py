# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/settings_service.py
======================================
Per-app settings: get/set/upsert + auto-mount `/admin/<app>/settings/` untuk
code-based apps (AppHelper) dan dynamic apps (AppManagerApp).

Kontrak schema (dipakai code-based apps via AppHelper.settings_schema):

    [
        {"key": "retention_days", "label": "Retention (days)",
         "value_type": "integer", "default": 30,
         "help_text": "Auto-purge older than N days"},
        {"key": "enable_email",   "label": "Email Notifications",
         "value_type": "boolean", "default": False},
    ]

Dynamic apps (dari AppManagerApp) dapat halaman setting default — user bisa
tambah key/value lewat form di UI admin.
"""
import logging
from flask import render_template, request, redirect, flash
from flask_login import login_required

from arasCore.lib.extensions import db

logger = logging.getLogger(__name__)


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def get_all_settings(app_id: int) -> list:
    """Return list of AppManagerSetting for an app, ordered."""
    from arasCore.arasAdmin.models import AppManagerSetting
    return (
        AppManagerSetting.query
        .filter_by(app_id=app_id)
        .order_by(AppManagerSetting.order, AppManagerSetting.key)
        .all()
    )


def get_setting(app_id: int, key: str, default=None):
    from arasCore.arasAdmin.models import AppManagerSetting
    row = AppManagerSetting.query.filter_by(app_id=app_id, key=key).first()
    return row.get_value() if row else default


def set_setting(app_id: int, key: str, value, value_type="string",
                label=None, help_text=None, order=0):
    """Upsert one setting row. Commits."""
    from arasCore.arasAdmin.models import AppManagerSetting
    row = AppManagerSetting.query.filter_by(app_id=app_id, key=key).first()
    if not row:
        row = AppManagerSetting(app_id=app_id, key=key, value_type=value_type,
                                label=label or key, help_text=help_text, order=order)
        db.session.add(row)
    else:
        row.value_type = value_type or row.value_type
        if label:     row.label = label
        if help_text: row.help_text = help_text
    row.set_value(value)
    db.session.commit()
    return row


def ensure_schema(app_id: int, schema: list):
    """
    Given a list of {key, label, value_type, default, help_text, order},
    create missing rows with default value. Doesn't overwrite existing values.
    """
    from arasCore.arasAdmin.models import AppManagerSetting
    existing = {s.key for s in get_all_settings(app_id)}
    created = 0
    for i, item in enumerate(schema or []):
        key = item.get("key")
        if not key or key in existing:
            continue
        row = AppManagerSetting(
            app_id=app_id,
            key=key,
            label=item.get("label") or key,
            value_type=item.get("value_type", "string"),
            help_text=item.get("help_text"),
            order=item.get("order", i),
        )
        row.set_value(item.get("default"))
        db.session.add(row)
        created += 1
    if created:
        db.session.commit()
    return created


def resolve_app_id_by_name(name: str):
    """Find AppManagerApp.id by slug. Returns None if not found (e.g. code-based apps)."""
    from arasCore.arasAdmin.models import AppManagerApp
    row = AppManagerApp.query.filter_by(name=name).first()
    return row.id if row else None


# ── Route factory ─────────────────────────────────────────────────────────────

def make_settings_view(app_name: str, app_title: str, schema: list = None,
                       is_dynamic: bool = False, registry_key: str = None):
    """
    Return a Flask view function for `/admin/<app_name>/settings/`.

    registry_key — helper.name for DB lookup (defaults to app_name).
                   Pass when admin_slug differs from name.
    """
    _db_key = registry_key or app_name

    @login_required
    def view():
        from arasCore.arasAdmin.models import AppManagerApp, AppManagerSetting

        app_row = AppManagerApp.query.filter_by(name=_db_key).first()
        if not app_row:
            app_row = AppManagerApp(
                name=_db_key,
                title=app_title,
                main_title=app_title,
                url=f"/{app_name}",
                endpoint=app_name,
                is_active=False,
                in_sidebar=False,
            )
            db.session.add(app_row)
            db.session.commit()

        if schema:
            ensure_schema(app_row.id, schema)

        if request.method == "POST":
            action = request.form.get("_action", "save")
            if action == "add" and is_dynamic:
                new_key   = (request.form.get("new_key") or "").strip()
                new_type  = request.form.get("new_type") or "string"
                new_label = request.form.get("new_label") or new_key
                if new_key:
                    set_setting(app_row.id, new_key, "", value_type=new_type, label=new_label)
                    flash(f"Setting '{new_key}' added.", "success")
            elif action == "delete":
                del_key = request.form.get("delete_key")
                row = AppManagerSetting.query.filter_by(app_id=app_row.id, key=del_key).first()
                if row:
                    db.session.delete(row)
                    db.session.commit()
                    flash(f"Setting '{del_key}' deleted.", "warning")
            else:
                # Save all fields posted as setting_<key>
                for field, raw in request.form.items():
                    if not field.startswith("setting_"):
                        continue
                    key = field[len("setting_"):]
                    row = AppManagerSetting.query.filter_by(app_id=app_row.id, key=key).first()
                    if row:
                        row.set_value(raw)
                # Boolean checkboxes: any row not in form => false
                bool_rows = AppManagerSetting.query.filter_by(
                    app_id=app_row.id, value_type="boolean"
                ).all()
                for r in bool_rows:
                    if f"setting_{r.key}" not in request.form:
                        r.set_value(False)
                db.session.commit()
                flash("Settings saved.", "success")
            return redirect(request.path)

        settings = get_all_settings(app_row.id)
        return render_template(
            "admin/aras_admin_settings.html",
            title=f"{app_title} — Settings",
            main_title=f"{app_title} Settings",
            app_name=app_name,
            app_title=app_title,
            settings=settings,
            is_dynamic=is_dynamic,
            value_types=("string", "text", "integer", "float", "boolean", "json"),
        )
    view.methods = ["GET", "POST"]
    return view


def mount_settings_route(flask_app_or_bp, app_name: str, app_title: str,
                         schema: list = None, is_dynamic: bool = False,
                         endpoint: str = None, registry_key: str = None):
    """Register `/admin/<app_name>/settings/` on a Flask app or blueprint."""
    url = f"/admin/{app_name}/settings/"
    ep  = endpoint or f"settings_{app_name}"
    try:
        view = make_settings_view(app_name, app_title, schema=schema, is_dynamic=is_dynamic, registry_key=registry_key)
        flask_app_or_bp.add_url_rule(url, endpoint=ep, view_func=view, methods=["GET", "POST"])
        logger.debug(f"[settings] mounted {url} (ep={ep})")
    except AssertionError:
        # Endpoint already registered — ignore
        logger.debug(f"[settings] {ep} already registered; skip")
    except Exception as e:
        logger.warning(f"[settings] failed to mount {url}: {e}")
