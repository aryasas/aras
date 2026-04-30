# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from arasCore.admin import admin_bp


@admin_bp.route("/trash/")
@login_required
def trash_list():
    from arasCore.lib.models.deletion_models import DeletedDoc
    from arasCore.lib.core.extensions import db
    from arasCore.auth import User

    page = request.args.get("page", 1, type=int)

    # Group by group_id to get summary per deletion operation
    subq = (db.session.query(
        DeletedDoc.group_id,
        db.func.max(DeletedDoc.deleted_at).label("deleted_at"),
        db.func.count(DeletedDoc.id).label("doc_count"),
        db.func.min(DeletedDoc.deleted_by_id).label("deleted_by_id"),
    )
    .group_by(DeletedDoc.group_id)
    .order_by(db.func.max(DeletedDoc.deleted_at).desc())
    .paginate(page=page, per_page=50, error_out=False))

    groups = []
    for row in subq.items:
        root = (DeletedDoc.query
                .filter_by(group_id=row.group_id, depth=0)
                .order_by(DeletedDoc.id.asc())
                .first())
        deleted_by = User.query.get(row.deleted_by_id) if row.deleted_by_id else None
        groups.append({
            "group_id":       row.group_id,
            "deleted_at":     row.deleted_at,
            "doc_count":      row.doc_count,
            "deleted_by_name": deleted_by.username if deleted_by else None,
            "root":           root,
        })

    return render_template("admin/trash/trash_list.html",
                           groups=groups,
                           pagination=subq)


@admin_bp.route("/trash/<group_id>/inspect/")
@login_required
def trash_inspect(group_id):
    from arasCore.lib.models.deletion_models import DeletedDoc
    docs = (DeletedDoc.query
            .filter_by(group_id=group_id)
            .order_by(DeletedDoc.depth.asc(), DeletedDoc.id.asc())
            .all())
    return jsonify({"docs": [
        {"doc_type": d.doc_type, "doc_id": d.doc_id, "depth": d.depth, "admin_url": d.admin_url}
        for d in docs
    ]})


@admin_bp.route("/trash/<group_id>/restore/", methods=["POST"])
@login_required
def trash_restore(group_id):
    from arasCore.lib.services.deletion_service import execute_restore
    try:
        execute_restore(group_id, user_id=current_user.id)
        flash("Records restored successfully.", "success")
    except Exception as ex:
        flash(f"Restore failed: {ex}", "danger")
    return redirect(url_for("admin.trash_list"))


@admin_bp.route("/trash/<group_id>/permanent-delete/", methods=["POST"])
@login_required
def trash_permanent_delete(group_id):
    from arasCore.lib.models.deletion_models import DeletedDoc
    from arasCore.lib.core.extensions import db
    DeletedDoc.query.filter_by(group_id=group_id).delete()
    db.session.commit()
    flash("Permanently deleted.", "warning")
    return redirect(url_for("admin.trash_list"))
