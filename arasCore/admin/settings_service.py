# -*- coding: utf-8 -*-
"""
arasCore/admin/settings_service.py
======================================
Per-app settings: get/set/upsert + two-level UI:

  /admin/<app>/settings/            — card-grid home (one card per section)
  /admin/<app>/settings/<section>/  — form for that section's keys

Schema contract (AppHelper.settings_schema):

    [
        {"key": "retention_days", "label": "Retention (days)",
         "value_type": "integer", "default": 30,
         "section": "cleanup",          # groups into a card
         "section_label": "Cleanup",    # card title (first item wins)
         "section_icon":  "fa-trash",   # card icon  (first item wins)
         "help_text": "Auto-purge older than N days"},
    ]

Items without "section" fall into a default "general" card.

Dynamic apps (AppManagerApp) get one "Custom Settings" section where
users can add/delete free-form key/value rows.

Framework injects a "General" card automatically with app metadata
(title, icon, description) editable from the UI.
"""
import logging
from flask import render_template, request, redirect, flash
from flask_login import login_required

from arasCore.lib.core.extensions import db

logger = logging.getLogger(__name__)

_VALUE_TYPES = ("string", "text", "integer", "float", "boolean", "json")

# ── CRUD helpers ──────────────────────────────────────────────────────────────

def get_all_settings(app_id: int) -> list:
    from arasCore.admin.models import AppManagerSetting
    return (
        AppManagerSetting.query
        .filter_by(app_id=app_id)
        .order_by(AppManagerSetting.order, AppManagerSetting.key)
        .all()
    )


def get_setting(app_id: int, key: str, default=None):
    from arasCore.admin.models import AppManagerSetting
    row = AppManagerSetting.query.filter_by(app_id=app_id, key=key).first()
    return row.get_value() if row else default


def set_setting(app_id: int, key: str, value, value_type="string",
                label=None, help_text=None, order=0, section=None):
    from arasCore.admin.models import AppManagerSetting
    row = AppManagerSetting.query.filter_by(app_id=app_id, key=key).first()
    if not row:
        row = AppManagerSetting(app_id=app_id, key=key, value_type=value_type,
                                label=label or key, help_text=help_text,
                                order=order)
        db.session.add(row)
    else:
        row.value_type = value_type or row.value_type
        if label:     row.label = label
        if help_text: row.help_text = help_text
    if section is not None and hasattr(row, "section"):
        row.section = section
    row.set_value(value)
    db.session.commit()
    return row


def ensure_schema(app_id: int, schema: list):
    from arasCore.admin.models import AppManagerSetting
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
        if hasattr(row, "section"):
            row.section = item.get("section") or "general"
        row.set_value(item.get("default"))
        db.session.add(row)
        created += 1
    if created:
        db.session.commit()
    return created


def resolve_app_id_by_name(name: str):
    from arasCore.admin.models import AppManagerApp
    row = AppManagerApp.query.filter_by(url=name).first()
    return row.id if row else None


# ── Section helpers ───────────────────────────────────────────────────────────

def _build_section_cards(schema: list, is_dynamic: bool, app_name: str) -> list:
    """
    Return list of card dicts for the settings home page.

    Always includes a "General" framework card. Schema items are grouped by
    their "section" key (default "general"). Dynamic apps get an extra card.
    """
    base_url = f"/admin/{app_name}/settings"

    # Framework-injected General card (app metadata)
    cards = [
        {
            "slug":        "general",
            "label":       "General",
            "icon":        "fa-info-circle",
            "description": "App title, icon, description, and status.",
            "url":         f"{base_url}/general/",
            "framework":   True,
        }
    ]

    # Build cards from schema sections
    seen = {}
    for item in (schema or []):
        sec  = item.get("section") or "app"
        if sec == "general":
            sec = "app"  # avoid collision with framework General card
        if sec not in seen:
            seen[sec] = {
                "slug":        sec,
                "label":       item.get("section_label") or sec.replace("-", " ").title(),
                "icon":        item.get("section_icon") or "fa-sliders-h",
                "description": item.get("section_description") or "",
                "url":         f"{base_url}/{sec}/",
                "framework":   False,
            }
        # propagate label/icon from first item that sets them
        if item.get("section_label") and seen[sec]["label"] == sec.replace("-", " ").title():
            seen[sec]["label"] = item["section_label"]
        if item.get("section_icon") and seen[sec]["icon"] == "fa-sliders-h":
            seen[sec]["icon"] = item["section_icon"]
        if item.get("section_description") and not seen[sec]["description"]:
            seen[sec]["description"] = item["section_description"]

    cards.extend(seen.values())

    if is_dynamic:
        cards.append({
            "slug":        "custom",
            "label":       "Custom Settings",
            "icon":        "fa-plus-circle",
            "description": "Free-form key/value settings added via the UI.",
            "url":         f"{base_url}/custom/",
            "framework":   False,
        })

    return cards


def _settings_for_section(app_id: int, section: str, schema: list) -> list:
    """Return AppManagerSetting rows belonging to a section slug."""
    all_rows = get_all_settings(app_id)
    schema_keys = {}
    for item in (schema or []):
        key = item.get("key")
        if not key:
            continue
        sec = item.get("section") or "app"
        if sec == "general":
            sec = "app"
        schema_keys[key] = sec

    result = []
    for row in all_rows:
        row_sec = getattr(row, "section", None) or schema_keys.get(row.key, "app")
        if row_sec == section:
            result.append(row)
    return result


# ── Framework General section (app metadata) ──────────────────────────────────

def _handle_general_post(app_row):
    """Save app-level metadata fields posted from the General section form."""
    title = (request.form.get("app_title") or "").strip()
    icon  = (request.form.get("app_icon") or "").strip()
    desc  = (request.form.get("app_description") or "").strip()
    order = request.form.get("app_menu_order", "")
    if title:
        app_row.title      = title
        app_row.main_title = title
    if icon is not None:
        app_row.icon = icon
    app_row.description = desc
    try:
        if order.strip():
            app_row.menu_order = int(order)
    except (ValueError, AttributeError):
        pass
    db.session.commit()
    flash("General settings saved.", "success")


# ── View factories ────────────────────────────────────────────────────────────

def make_settings_home_view(app_name: str, app_title: str,
                            schema: list = None, is_dynamic: bool = False,
                            registry_key: str = None):
    """
    View for `/admin/<app_name>/settings/` — card-grid index of all sections.
    """
    _db_key = registry_key or app_name

    @login_required
    def view():
        from arasCore.admin.models import AppManagerApp
        app_row = AppManagerApp.query.filter_by(url=_db_key).first()
        if not app_row:
            app_row = _ensure_app_row(_db_key, app_name, app_title)

        if schema:
            ensure_schema(app_row.id, schema)

        cards = _build_section_cards(schema or [], is_dynamic, app_name)

        return render_template(
            "admin/setting/setting_app_settings.html",
            title=f"{app_title} — Settings",
            main_title=f"{app_title} — Settings",
            app_name=app_name,
            app_title=app_title,
            app_row=app_row,
            cards=cards,
            home_url=f"/admin/{app_name}/",
        )
    return view


def make_settings_section_view(app_name: str, app_title: str, section: str,
                               schema: list = None, is_dynamic: bool = False,
                               registry_key: str = None):
    """
    View for `/admin/<app_name>/settings/<section>/` — form for one section.
    """
    _db_key = registry_key or app_name
    settings_home = f"/admin/{app_name}/settings/"

    @login_required
    def view():
        from arasCore.admin.models import AppManagerApp, AppManagerSetting

        app_row = AppManagerApp.query.filter_by(url=_db_key).first()
        if not app_row:
            app_row = _ensure_app_row(_db_key, app_name, app_title)

        if schema:
            ensure_schema(app_row.id, schema)

        # ── POST handling ──────────────────────────────────────────────────
        if request.method == "POST":
            action = request.form.get("_action", "save")

            if section == "general":
                _handle_general_post(app_row)

            elif section == "custom" and is_dynamic:
                if action == "add":
                    new_key   = (request.form.get("new_key") or "").strip()
                    new_type  = request.form.get("new_type") or "string"
                    new_label = request.form.get("new_label") or new_key
                    if new_key:
                        set_setting(app_row.id, new_key, "",
                                    value_type=new_type, label=new_label,
                                    section="custom")
                        flash(f"Setting '{new_key}' added.", "success")
                elif action == "delete":
                    del_key = request.form.get("delete_key")
                    row = AppManagerSetting.query.filter_by(
                        app_id=app_row.id, key=del_key).first()
                    if row:
                        db.session.delete(row)
                        db.session.commit()
                        flash(f"Setting '{del_key}' deleted.", "warning")
                else:
                    _save_section_settings(app_row.id, section, schema)

            else:
                _save_section_settings(app_row.id, section, schema)

            return redirect(request.path)

        # ── GET: build context ────────────────────────────────────────────
        if section == "general":
            section_settings = []  # rendered inline from app_row fields
        else:
            section_settings = _settings_for_section(app_row.id, section, schema)

        # Resolve section meta from cards list
        cards = _build_section_cards(schema or [], is_dynamic, app_name)
        card  = next((c for c in cards if c["slug"] == section), None)
        section_label = card["label"] if card else section.replace("-", " ").title()
        section_icon  = card["icon"]  if card else "fa-cog"

        return render_template(
            "admin/setting/setting_settings_section.html",
            title=f"{app_title} — {section_label}",
            main_title=section_label,
            app_name=app_name,
            app_title=app_title,
            app_row=app_row,
            section=section,
            section_label=section_label,
            section_icon=section_icon,
            settings=section_settings,
            is_dynamic=is_dynamic and section == "custom",
            is_general=section == "general",
            value_types=_VALUE_TYPES,
            settings_home=settings_home,
        )
    view.methods = ["GET", "POST"]
    return view


# ── Internal helpers ──────────────────────────────────────────────────────────

def _ensure_app_row(db_key, app_name, app_title):
    from arasCore.admin.models import AppManagerApp
    app_row = AppManagerApp(
        name=db_key, title=app_title, main_title=app_title,
        url=f"/{app_name}", endpoint=app_name,
        is_active=False, in_sidebar=False,
    )
    db.session.add(app_row)
    db.session.commit()
    return app_row


def _save_section_settings(app_id: int, section: str, schema: list):
    from arasCore.admin.models import AppManagerSetting
    # Determine keys belonging to this section
    schema_keys_in_section = set()
    for item in (schema or []):
        key = item.get("key")
        if not key:
            continue
        sec = item.get("section") or "app"
        if sec == "general":
            sec = "app"
        if sec == section:
            schema_keys_in_section.add(key)

    for field, raw in request.form.items():
        if not field.startswith("setting_"):
            continue
        key = field[len("setting_"):]
        if schema_keys_in_section and key not in schema_keys_in_section:
            continue
        row = AppManagerSetting.query.filter_by(app_id=app_id, key=key).first()
        if row:
            row.set_value(raw)

    # Boolean checkboxes for this section
    all_rows = get_all_settings(app_id)
    schema_keys_map = {}
    for item in (schema or []):
        k = item.get("key")
        if k:
            sec = item.get("section") or "app"
            if sec == "general":
                sec = "app"
            schema_keys_map[k] = sec

    for r in all_rows:
        if r.value_type != "boolean":
            continue
        row_sec = getattr(r, "section", None) or schema_keys_map.get(r.key, "app")
        if row_sec == section and f"setting_{r.key}" not in request.form:
            r.set_value(False)

    db.session.commit()
    flash("Settings saved.", "success")


# ── Mount helper ──────────────────────────────────────────────────────────────

def mount_settings_route(flask_app_or_bp, app_name: str, app_title: str,
                         schema: list = None, is_dynamic: bool = False,
                         endpoint: str = None, registry_key: str = None):
    """
    Register settings home + wildcard section route on a Flask app or blueprint.

      GET  /admin/<app_name>/settings/            → card-grid index
      GET  /admin/<app_name>/settings/<section>/  → section form
      POST /admin/<app_name>/settings/<section>/  → save
    """
    home_url = f"/admin/{app_name}/settings/"
    sec_url  = f"/admin/{app_name}/settings/<section>/"
    ep_home  = endpoint or f"settings_{app_name}"
    ep_sec   = f"{ep_home}_section"

    try:
        home_view = make_settings_home_view(
            app_name, app_title, schema=schema,
            is_dynamic=is_dynamic, registry_key=registry_key,
        )
        flask_app_or_bp.add_url_rule(
            home_url, endpoint=ep_home, view_func=home_view, methods=["GET"],
        )
        logger.debug(f"[settings] mounted {home_url} (ep={ep_home})")
    except AssertionError:
        logger.debug(f"[settings] {ep_home} already registered; skip")
    except Exception as e:
        logger.warning(f"[settings] home mount failed for {home_url}: {e}")

    try:
        # We need a real closure that reads section from the URL arg
        _schema     = schema
        _is_dyn     = is_dynamic
        _reg_key    = registry_key
        _app_name   = app_name
        _app_title  = app_title

        @login_required
        def section_dispatcher(section):
            return make_settings_section_view(
                _app_name, _app_title, section=section,
                schema=_schema, is_dynamic=_is_dyn, registry_key=_reg_key,
            )()
        section_dispatcher.methods = ["GET", "POST"]

        flask_app_or_bp.add_url_rule(
            sec_url, endpoint=ep_sec,
            view_func=section_dispatcher, methods=["GET", "POST"],
        )
        logger.debug(f"[settings] mounted {sec_url} (ep={ep_sec})")
    except AssertionError:
        logger.debug(f"[settings] {ep_sec} already registered; skip")
    except Exception as e:
        logger.warning(f"[settings] section mount failed for {sec_url}: {e}")


# ── Legacy shim — keep old make_settings_view callable ───────────────────────

def make_settings_view(app_name: str, app_title: str, schema: list = None,
                       is_dynamic: bool = False, registry_key: str = None):
    """Backward-compat alias → make_settings_home_view."""
    return make_settings_home_view(
        app_name, app_title, schema=schema,
        is_dynamic=is_dynamic, registry_key=registry_key,
    )
