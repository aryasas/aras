# -*- coding: utf-8 -*-
"""
aras/app_soc/manifest.py
========================
AppHelper declaration untuk app_soc.
Framework membaca file ini saat startup untuk:
  - Mendaftarkan model SOC ke universal API (/api/soc/<resource>/)
  - Mounting custom routes (feed, friendship, conversation) di /api/soc/
  - Membuat admin routes /admin/soc/<resource>/

Semua logic bisnis tetap di services/. Tidak ada route definition di sini —
framework yang mendaftarkan semuanya berdasarkan deklarasi ini.
"""
from arasCore.lib.app_helper import AppHelper, ResourceDef, CustomRoute

from aras.app_soc.models import (
    SocPost, SocProfile, SocFriendship, SocComment,
    SocLike, SocConversation, SocMessage, SocUserPref,
)


# ── Serializers ───────────────────────────────────────────────────────────────

def _post_serializer(p):
    return {
        "id":             p.id,
        "author_id":      p.author_id,
        "author_username": p.author.username if p.author else None,
        "content":        p.content,
        "visibility":     p.visibility,
        "is_edited":      p.is_edited,
        "shared_from_id": p.shared_from_id,
        "like_count":     p.like_count,
        "comment_count":  p.comment_count,
        "share_count":    p.share_count,
        "deleted_at":     p.deleted_at.isoformat() if p.deleted_at else None,
        "created_at":     p.created_at.isoformat() if p.created_at else None,
    }


def _profile_serializer(profile):
    user = profile.user if hasattr(profile, "user") else None
    return {
        "id":            profile.id,
        "user_id":       profile.user_id,
        "username":      user.username if user else None,
        "bio":           profile.bio,
        "location":      profile.location,
        "website":       profile.website,
        "avatar_url":    profile.avatar_url,
        "cover_url":     profile.cover_url,
        "post_count":    profile.post_count,
        "friend_count":  profile.friend_count,
        "privacy_profile": profile.privacy_profile,
    }


def _friendship_serializer(f):
    return {
        "id":           f.id,
        "from_user_id": f.from_user_id,
        "to_user_id":   f.to_user_id,
        "status":       f.status,
        "created_at":   f.created_at.isoformat() if f.created_at else None,
    }


def _comment_serializer(c):
    return {
        "id":             c.id,
        "post_id":        c.post_id,
        "parent_id":      c.parent_id,
        "author_id":      c.author_id,
        "author_username": c.author.username if c.author else None,
        "content":        c.content,
        "like_count":     c.like_count,
        "deleted_at":     c.deleted_at.isoformat() if c.deleted_at else None,
        "created_at":     c.created_at.isoformat() if c.created_at else None,
    }


def _conversation_serializer(conv):
    return {
        "id":              conv.id,
        "created_by":      conv.created_by,
        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        "created_at":      conv.created_at.isoformat() if conv.created_at else None,
    }


def _message_serializer(m):
    return {
        "id":              m.id,
        "conversation_id": m.conversation_id,
        "sender_id":       m.sender_id,
        "sender_username": m.sender.username if m.sender else None,
        "body":            m.body,
        "deleted_at":      m.deleted_at.isoformat() if m.deleted_at else None,
        "created_at":      m.created_at.isoformat() if m.created_at else None,
    }


# ── Custom route handlers ─────────────────────────────────────────────────────
# Handler ditulis di sini agar framework bisa mount ke /api/soc/<path>.
# Logic bisnis tetap di services/.

def _handle_feed():
    from flask import request, jsonify
    from flask_login import current_user
    from aras.app_soc.services.feed_service import get_feed
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 20, type=int)
    paginated = get_feed(current_user.id, page=page, per_page=per_page)
    return jsonify({
        "ok":   True,
        "data": [_post_serializer(p) for p in paginated.items],
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
        "data": [_post_serializer(p) for p in paginated.items],
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
        ResourceDef("posts",         SocPost,         serializer=_post_serializer,         admin_list=True),
        ResourceDef("profiles",      SocProfile,      serializer=_profile_serializer,      admin_list=True),
        ResourceDef("friendships",   SocFriendship,   serializer=_friendship_serializer,   admin_list=True),
        ResourceDef("comments",      SocComment,      serializer=_comment_serializer,      admin_list=False),
        ResourceDef("conversations", SocConversation, serializer=_conversation_serializer, admin_list=False),
        ResourceDef("messages",      SocMessage,      serializer=_message_serializer,      admin_list=False),
        ResourceDef("likes",         SocLike,                                              admin_list=False),
        ResourceDef("preferences",   SocUserPref,                                          admin_list=False),
    ],
    custom_routes=[
        CustomRoute("/feed",           _handle_feed,          methods=["GET"], require_auth=True),
        CustomRoute("/feed/public",    _handle_feed_public,   methods=["GET"], require_auth=False),
        CustomRoute("/friends",        _handle_friends_list,  methods=["GET"], require_auth=True),
        CustomRoute("/friends/request", _handle_friend_request, methods=["POST"], require_auth=True),
        CustomRoute("/search/users",   _handle_search_users,  methods=["GET"], require_auth=False),
    ],
)
