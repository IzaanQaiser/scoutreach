# KNOWN_GAPS

## Auth
- Phase 1 `/me` currently reflects authenticated token identity but does not yet hydrate full user profile fields from `users` table.
- Supabase token verification is implemented, but development/test fallback token path still exists by design (`ALLOW_DEV_AUTH=true` in non-production environments only).
- Frontend login/signup UI, onboarding routes, and dashboard route guards are not implemented yet; see `/docs/auth_onboarding_build_blueprint.md` for the formal build plan.

## Database
- Migration files exist, but no migration runner CLI is wired yet; execution is manual via SQL tooling.

## Product Flow
- Outreach review/update/regenerate/send APIs are now implemented, but send processing is still request-thread/in-process (no durable external queue/worker).

## Phase 2 Scraper
- Current scraper integration is a deterministic stub in `backend/app/integrations/playwright_scraper.py`; real Playwright YC scraping is deferred.
- Background task execution is in-process; no durable external worker/queue exists yet.

## Run API Surface
- Core run and outreach workflow endpoints are implemented through send (`POST /runs`, run status polling, company review, outreach generation, outreach review/regenerate, send-approved/single-send); broader run listing/detail endpoints remain unimplemented.

## Phase 3 Provider Integrations
- Gemini dossier/outreach and Hunter enrichment clients are deterministic stubs for now; real provider API traffic, credentials, and retry/backoff tuning are deferred.
- Provider failure details are currently persisted in `companies.raw_scraped_data.provider_errors`; no dedicated provider-error table exists yet.

## Sending Safety
- `send-approved` and single-send include quota checks plus retry/backoff for simulated transient failures, but provider throttling and fairness are process-local and not coordinated across replicas.

## Regeneration History
- Regeneration attempt metadata is now tracked in `outreach_regeneration_events`, but full message version history (before/after draft diffs) is still not modeled.
