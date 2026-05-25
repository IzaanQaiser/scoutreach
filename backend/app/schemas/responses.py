"""Common API response helpers."""

from __future__ import annotations

from typing import Any


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data}


def error_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
