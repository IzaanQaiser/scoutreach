"""FastAPI application entrypoint for ScoutReach backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.db.supabase_client import build_supabase_client
from app.middleware.errors import register_error_handlers
from app.utils.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    app.state.settings = settings
    app.state.supabase_client = build_supabase_client(settings)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ScoutReach API",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_error_handlers(app)

    app.include_router(health_router)
    app.include_router(me_router)

    return app


app = create_app()
