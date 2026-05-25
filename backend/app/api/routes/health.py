"""Healthcheck route."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.responses import success_response


router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    return success_response({"status": "ok"})
