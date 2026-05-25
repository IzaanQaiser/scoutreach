# KNOWN_GAPS

## Auth
- Phase 1 `/me` currently reflects authenticated token identity but does not yet hydrate full user profile fields from `users` table.
- Supabase token verification is implemented, but development/test fallback token path still exists by design (`ALLOW_DEV_AUTH=true` in non-production environments only).

## Database
- Migration files exist, but no migration runner CLI is wired yet; execution is manual via SQL tooling.

## Product Flow
- Dossier generation, founder enrichment, swipe flow, and sending orchestration are not implemented yet (Phase 3+).

## Phase 2 Scraper
- Current scraper integration is a deterministic stub in `backend/app/integrations/playwright_scraper.py`; real Playwright YC scraping is deferred.
- Background task execution is in-process; no durable external worker/queue exists yet.

## Run API Surface
- Phase 2 includes `POST /runs` and `GET /runs/{run_id}/status`; broader run listing/detail endpoints remain unimplemented.
