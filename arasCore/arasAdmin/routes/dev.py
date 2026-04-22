# -*- coding: utf-8 -*-
from flask import render_template
from flask_login import login_required, current_user

from arasCore.arasAdmin import arasAdmin_bp


@arasAdmin_bp.route("/dev")
@login_required
def dev():
    return render_template("admin/dev.html", main_title="Dev Page", user=current_user)
