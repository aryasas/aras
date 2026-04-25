# -*- coding: utf-8 -*-
from flask import request, jsonify, current_app
from flask_login import login_required
from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db

@arasAdmin_bp.route("/settings/menu/data")
@login_required
def menu_data():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    def node_dict(t):
        return {
            "id": t.id, "name": t.name, "title": t.get_menu_title(),
            "icon": t.menu_icon or "fa-table", "show_in_menu": t.show_in_menu,
            "menu_order": t.menu_order, "db_backed": True,
            "is_group": t.page_type == "group", "children": [],
        }
    result = []
    for app in AppManagerApp.query.order_by(AppManagerApp.menu_order).all():
        tables = AppManagerTable.query.filter_by(app_id=app.id).order_by(AppManagerTable.menu_order).all()
        tbl_map = {t.id: node_dict(t) for t in tables}
        roots = []
        for t in tables:
            node = tbl_map[t.id]
            if t.parent_table_id and t.parent_table_id in tbl_map:
                tbl_map[t.parent_table_id]["children"].append(node)
            else: roots.append(node)
        result.append({
            "id": app.id, "name": app.slug, "title": app.title,
            "icon": app.icon or "fa-cubes", "menu_order": app.menu_order or 0,
            "in_sidebar": app.in_sidebar, "db_backed": True, "tables": roots,
        })
    return jsonify(result)

@arasAdmin_bp.route("/settings/menu/save", methods=["POST"])
@login_required
def menu_save():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    data = request.get_json(force=True)
    try:
        for app_node in data.get("apps", []):
            aid = int(app_node.get("id", 0))
            app = db.session.get(AppManagerApp, aid)
            if app:
                app.menu_order = int(app_node.get("menu_order") or 0)
                app.in_sidebar = bool(app_node.get("in_sidebar", True))

        def save_table_nodes(nodes, parent_id=None):
            for order, node in enumerate(nodes):
                nid = int(node.get("id") or 0)
                if nid > 0:
                    tbl = db.session.get(AppManagerTable, nid)
                    if tbl:
                        tbl.menu_order, tbl.parent_table_id = order, parent_id
                save_table_nodes(node.get("children", []), nid if nid > 0 else parent_id)

        for app_node in data.get("apps", []): save_table_nodes(app_node.get("tables", []), None)
        db.session.commit()
        clear_cache()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
