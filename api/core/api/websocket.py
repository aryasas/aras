"""
Purpose: WebSocket endpoint for real-time push notifications.
Context: Registered in main.py. Frontend connects to /api/v1/ws.
Impact: Enables live updates for audit logs, workflow, and dashboard refresh.
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

router = APIRouter()

# Channel → set of connected websockets
_connections: Dict[str, Set[WebSocket]] = {}

# Module-level broadcast function consumed by AuditManager and WorkflowManager
async def broadcast(channel: str, payload: dict):
    """Push a JSON message to all subscribers of a channel."""
    dead = set()
    for ws in list(_connections.get(channel, set())):
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections.get(channel, set()).discard(ws)


def broadcast_sync(channel: str, payload: dict):
    """Sync wrapper — schedules broadcast on the running event loop if available."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(channel, payload))
    except RuntimeError:
        pass  # No event loop in sync context (e.g. test runner) — skip silently


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    channel: str = Query("global"),
    token: str = Query(None),
):
    """
    Authenticated WebSocket. Clients subscribe to a named channel.

    Channels:
      - global        — catch-all
      - audit         — new ActivityLog entries
      - workflow      — state machine transitions
      - dashboard     — widget data refresh triggers
    """
    # Verify JWT before accepting
    from core.lib.settings import settings

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            sub = payload.get("sub")
            if not sub:
                await ws.close(code=4001)
                return
        except JWTError:
            await ws.close(code=4001)
            return
    # Allow unauthenticated for dev (no token provided) — restrict in prod via ARAS_MODE
    from core.lib.settings import settings as _s
    if not token and not _s.DEBUG:
        await ws.close(code=4001)
        return

    await ws.accept()
    _connections.setdefault(channel, set()).add(ws)
    _connections.setdefault("global", set()).add(ws)
    try:
        while True:
            # Keep connection alive; ignore incoming messages
            await ws.receive_text()
    except WebSocketDisconnect:
        _connections.get(channel, set()).discard(ws)
        _connections.get("global", set()).discard(ws)
