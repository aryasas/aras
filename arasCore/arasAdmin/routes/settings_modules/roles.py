# -*- coding: utf-8 -*-
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db
from arasCore.auth import User

@arasAdmin_bp.route("/roles/new", methods=["POST"])
@login_required
def role_new():
    from arasCore.permissions import Role
    name = (request.form.get("name") or "").strip()
    slug = (request.form.get("slug") or name.lower().replace(" ", "_")).strip()
    if not name or not slug: flash("Name and slug are required.", "warning")
    elif Role.query.filter_by(slug=slug).first(): flash(f"Role '{slug}' already exists.", "warning")
    else:
        db.session.add(Role(name=name, slug=slug, description=request.form.get("description")))
        db.session.commit()
        flash(f"Role '{name}' created.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")

@arasAdmin_bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
def role_edit(role_id):
    from arasCore.permissions import Role, Permission, UserRole
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.order_by(Permission.app_slug, Permission.slug).all()
    all_users = User.query.order_by(User.username).all()

    if request.method == "POST":
        action = request.form.get("_action")
        if action == "permissions":
            perm_ids = [int(x) for x in request.form.getlist("perm_ids")]
            role.permissions = [p for p in all_permissions if p.id in perm_ids]
            db.session.commit()
            flash("Permissions updated.", "success")
        elif action == "users":
            user_ids = [int(x) for x in request.form.getlist("user_ids")]
            UserRole.query.filter_by(role_id=role_id).delete()
            for uid in user_ids: db.session.add(UserRole(user_id=uid, role_id=role_id))
            db.session.commit()
            flash("Users updated.", "success")
        return redirect(url_for("admin.role_edit", role_id=role_id))

    grouped_perms = {}
    for p in all_permissions: grouped_perms.setdefault(p.app_slug, []).append(p)
    return render_template(
        "admin/views/adm_auth_role_edit.html",
        title=f"Edit Role — {role.name}", main_title="Roles",
        role=role, all_permissions=all_permissions, grouped_perms=grouped_perms,
        role_perm_ids=[p.id for p in role.permissions],
        all_users=all_users, assigned_user_ids=[ur.user_id for ur in UserRole.query.filter_by(role_id=role_id).all()],
        list_url=url_for("admin.settings") + "?panel=panel-roles",
    )
