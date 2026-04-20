# -*- coding: utf-8 -*-
from arasCore.lib.app_helper import AppHelper, ResourceDef, CustomRoute

from aras.app_soc.models import (
    SocPost, SocProfile, SocFriendship, SocComment,
    SocLike, SocConversation, SocMessage, SocUserPref,
)


# ── Custom route handlers ─────────────────────────────────────────────────────

def _handle_feed():
    from flask import request, jsonify
    from flask_login import current_user
    from aras.app_soc.services.feed_service import get_feed
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 20, type=int)
    paginated = get_feed(current_user.id, page=page, per_page=per_page)
    return jsonify({
        "ok":   True,
        "data": [p.to_dict() for p in paginated.items],
        "meta": {"page": paginated.page, "pages": paginated.pages, "total": paginated.total},
    })


def _handle_feed_public():
    from flask import request, jsonify
    from aras.app_soc.services.feed_service import get_public_feed
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 20, type=int)
    paginated = get_public_feed(page=page, per_page=per_page)
    return jsonify({
        "ok":   True,
        "data": [p.to_dict() for p in paginated.items],
        "meta": {"page": paginated.page, "pages": paginated.pages, "total": paginated.total},
    })


def _handle_friends_list():
    from flask import jsonify
    from flask_login import current_user
    from arasCore.auth import User
    from aras.app_soc.services import friendship_service as fs
    friend_ids = fs.get_friends(current_user.id)
    users = User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
    return jsonify({"ok": True, "data": [
        {"id": u.id, "username": u.username} for u in users
    ]})


def _handle_friend_request():
    from flask import request, jsonify
    from flask_login import current_user
    from aras.app_soc.services import friendship_service as fs
    data    = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "user_id required"}), 400
    f, created = fs.send_request(current_user.id, user_id)
    return jsonify({"ok": True, "data": {"status": f.status, "created": created}}), 201 if created else 200


def _handle_search_users():
    from flask import request, jsonify
    from arasCore.auth import User
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"ok": True, "data": []})
    users = User.query.filter(
        User.is_active == True,
        User.username.ilike(f"%{q}%"),
    ).limit(20).all()
    return jsonify({"ok": True, "data": [{"id": u.id, "username": u.username} for u in users]})


# ── AppHelper instance — dibaca oleh framework ────────────────────────────────

helper = AppHelper(
    name="soc",
    title="Social",
    admin_icon="fa-users",
    admin_order=10,
    resources=[
        ResourceDef("posts",         SocPost,         admin_list=True),
        ResourceDef("profiles",      SocProfile,      admin_list=True),
        ResourceDef("friendships",   SocFriendship,   admin_list=True),
        ResourceDef("comments",      SocComment,      admin_list=False),
        ResourceDef("conversations", SocConversation, admin_list=False),
        ResourceDef("messages",      SocMessage,      admin_list=False),
        ResourceDef("likes",         SocLike,         admin_list=False),
        ResourceDef("preferences",   SocUserPref,     admin_list=False),
    ],
    custom_routes=[
        CustomRoute("/feed",            _handle_feed,           methods=["GET"], require_auth=True),
        CustomRoute("/feed/public",     _handle_feed_public,    methods=["GET"], require_auth=False),
        CustomRoute("/friends",         _handle_friends_list,   methods=["GET"], require_auth=True),
        CustomRoute("/friends/request", _handle_friend_request, methods=["POST"], require_auth=True),
        CustomRoute("/search/users",    _handle_search_users,   methods=["GET"], require_auth=False),
    ],
)
