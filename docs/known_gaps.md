# KNOWN_GAPS

## Auth
- Phase 1 `/me` currently reflects authenticated token identity but does not yet hydrate full user profile fields from `users` table.
- Supabase token verification is implemented, but development/test fallback token path still exists by design (`ALLOW_DEV_AUTH=true` in non-production environments only).

## Database
- Migration files exist, but no migration runner CLI is wired yet; execution is manual via SQL tooling.

## Product Flow
- Sending orchestration is not implemented yet (Phase 6+).
- Frontend swipe UI wiring for the new Phase 4 review endpoints is still pending.

## Phase 2 Scraper
- Current scraper integration is a deterministic stub in `backend/app/integrations/playwright_scraper.py`; real Playwright YC scraping is deferred.
- Background task execution is in-process; no durable external worker/queue exists yet.

## Run API Surface
- `POST /runs`, `GET /runs/{run_id}/status`, and Phase 4 company review endpoints are implemented; broader run listing/detail endpoints remain unimplemented.

## Phase 3 Provider Integrations
- Gemini dossier and Hunter enrichment clients are deterministic stubs for now; real provider API traffic, credentials, and retry/backoff tuning are deferred.
- Provider failure details are currently persisted in `companies.raw_scraped_data.provider_errors`; no dedicated provider-error table exists yet.
