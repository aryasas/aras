# -*- coding: utf-8 -*-
from flask import jsonify, g, request, render_template
from flask_login import login_required, current_user
from arasCore.admin import admin_bp
from arasCore.admin.services import build_sidebar_menu
from arasCore.admin.models import ArasSystemSetting, AppManagerTable
from arasCore.lib.services.api_handler import get_api_registry
from arasCore.admin.services import _get_child_tables_for_model
from arasCore.lib.ui.label_utils import find_ref_model, row_display

@admin_bp.route('/api/ui/init', methods=['GET'])
@login_required
def ui_init():
    menu = build_sidebar_menu()
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }
    return jsonify({"menu": menu, "user": user_data})

@admin_bp.route('/api/ui/resource-config/<path:resource>', methods=['GET'])
@login_required
def ui_resource_config(resource):
    from arasCore.admin.models import AppManagerTable, AppManagerApp
    from arasCore.admin.home_service import _count_rows
    
    # 1. Check for Group (Module Home) first
    # Resource might be 'accounting' or 'erp/accounting'
    grp_rec = AppManagerTable.query.filter_by(page_type="group", is_active=True).filter(
        (AppManagerTable.url_suffix == f"/{resource}") | 
        (AppManagerTable.name == resource) |
        (AppManagerTable.db_table_name == resource)
    ).first()
    
    if grp_rec:
        app_rec = AppManagerApp.query.get(grp_rec.app_id)
        children = (
            AppManagerTable.query
            .filter_by(app_id=app_rec.id, parent_table_id=grp_rec.id, is_active=True, show_in_menu=True)
            .order_by(AppManagerTable.menu_order)
            .all()
        )
        tiles = []
        for t in children:
            tiles.append({
                "title": t.get_menu_title(),
                "icon": t.icon or t.menu_icon or "fa-table",
                "url": app_rec.admin_url(t),
                "page_type": t.page_type or "list",
                "count": _count_rows(t.get_db_table_name(app_rec.slug)) if (t.page_type or "list") == "list" else None
            })
        return jsonify({
            "viewType": "appHome",
            "title": grp_rec.get_menu_title(),
            "tiles": tiles,
            "isSubmodule": True,
            "backUrl": f"/admin/{app_rec.url}/?view_engine=react"
        })

    registry = get_api_registry()
    if resource not in registry:
        return jsonify({"error": "Resource not found"}), 404
        
    cfg = registry[resource]
    model = cfg['model']
    
    columns = []
    fields = []
    
    # Try getting explicit config from model if available
    try:
        from arasCore.admin.table_registry import get_table_for_model
        tbl = get_table_for_model(model.__name__)
        if tbl:
            for col in tbl.columns:
                columns.append({"name": col.name, "label": col.label})
                field_def = {"name": col.name, "label": col.label, "type": col.field_type, "required": col.required}
                
                if col.field_type == 'relation':
                    raw_fk = None
                    if col.relation_system_table:
                        raw_fk = col.relation_system_table
                    elif col.relation_table:
                        raw_fk = col.relation_table.db_table_name or col.relation_table.name
                    
                    if raw_fk:
                        ref = find_ref_model(raw_fk)
                        if ref:
                            try:
                                choices = [{"id": r.id, "label": row_display(r)} for r in ref.query.all()]
                                field_def['choices'] = choices
                            except Exception:
                                pass
                fields.append(field_def)
    except Exception as e:
        print("Error reading table registry:", e)
        # Fallback reflection
        for c in model.__table__.columns:
            if c.name in ['created_at', 'updated_at']:
                continue
            columns.append({"name": c.name, "label": c.name.replace('_', ' ').title()})
            fields.append({"name": c.name, "label": c.name.replace('_', ' ').title(), "type": str(c.type)})
            
    cts = _get_child_tables_for_model(model)
    child_tables_meta = []
    for ct in cts:
        columns_meta = []
        if "inline_columns" in ct:
            for c in ct["inline_columns"]:
                columns_meta.append({
                    "name": c["name"],
                    "label": c["label"],
                    "type": c["type"],
                    "required": c.get("required", False),
                    "fk_table": c.get("fk_table"),
                    "fk_api_url": c.get("fk_api_url"),
                    "fk_options": c.get("fk_options", [])
                })
        
        child_tables_meta.append({
            "name": ct["model_name"],
            "title": ct["title"],
            "columns": columns_meta
        })

    return jsonify({
        "columns": columns if columns else getattr(cfg, 'columns', []),
        "fields": fields if fields else getattr(cfg, 'fields', []),
        "child_tables": child_tables_meta
    })
