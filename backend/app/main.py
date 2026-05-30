"""FastAPI application entrypoint for ScoutReach backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes.companies import router as companies_router
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.runs import router as runs_router
from app.db.run_repository import InMemoryRunRepository, SupabaseRunRepository
from app.db.supabase_client import build_supabase_client
from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.hunter_client import HunterEmailClient
from app.integrations.playwright_scraper import PlaywrightYcScraper
from app.middleware.errors import register_error_handlers
from app.services.company_service import CompanyService
from app.services.outreach_generation_service import OutreachGenerationService
from app.services.run_service import RunService
from app.utils.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    app.state.settings = settings
    app.state.supabase_client = build_supabase_client(settings)
    if settings.environment == "test":
        run_repository = InMemoryRunRepository()
    else:
        run_repository = SupabaseRunRepository(app.state.supabase_client)
    app.state.run_repository = run_repository
    app.state.scraper = PlaywrightYcScraper()
    app.state.gemini_client = GeminiDossierClient()
    app.state.hunter_client = HunterEmailClient()
    app.state.run_service = RunService(
        repository=run_repository,
        scraper=app.state.scraper,
        gemini_client=app.state.gemini_client,
        hunter_client=app.state.hunter_client,
    )
    app.state.company_service = CompanyService(repository=run_repository)
    app.state.outreach_generation_service = OutreachGenerationService(
        repository=run_repository,
        gemini_client=app.state.gemini_client,
    )
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
    app.include_router(runs_router)
    app.include_router(companies_router)

    return app


app = create_app()
