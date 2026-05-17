from typing import Any, Optional


def ok(data: Optional[Any] = None, message: Optional[str] = None) -> dict:
    return {"success": True, "data": data, "message": message, "error": None}


def err(message: str, detail: Optional[Any] = None) -> dict:
    return {"success": False, "data": None, "message": None, "error": {"message": message, "detail": detail}}
