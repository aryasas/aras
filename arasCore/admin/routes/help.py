# -*- coding: utf-8 -*-
from flask import render_template
from flask_login import login_required, current_user
from arasCore.admin import admin_bp

@admin_bp.route("/help")
@login_required
def help_page():
    return render_template(
        "admin/base/base_help.html",
        title="Help & Documentation",
        main_title="Framework Help",
        user=current_user
    )
