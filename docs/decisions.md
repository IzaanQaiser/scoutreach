# DECISIONS

## 2026-05-17
Decision:
Manual review required before sending.

Reason:
Safer for public beta and reduces spam risk.

---

## 2026-05-17
Decision:
Use JSONB heavily in MVP schema.

Reason:
Faster iteration speed and schema flexibility.

---

## 2026-05-24
Decision:
Phase 1 backend foundation uses FastAPI app shell with explicit API response envelope and centralized error handlers.

Reason:
Keeps route behavior predictable and aligned with API contract from day one.

---

## 2026-05-24
Decision:
Core schema is delivered via SQL migration files (`0001_core_tables_up.sql` / `0001_core_tables_down.sql`) with ownership FKs, status checks, and `updated_at` triggers.

Reason:
Meets migration/reversibility rules and enforces table-level invariants early.

---

## 2026-05-24
Decision:
Auth baseline supports strict bearer auth with a development-only fallback token gate (`ALLOW_DEV_AUTH`) for local/testing workflows.

Reason:
Enables immediate integration testing without requiring live Supabase Auth traffic, while still preserving server-side auth dependency boundaries.

---

## 2026-05-25
Decision:
Phase 2 run pipeline uses a repository abstraction with a Supabase-backed implementation for non-test environments and an in-memory implementation for test runs.

Reason:
Allows deterministic integration testing without paid network dependencies while preserving production persistence behavior.

---

## 2026-05-25
Decision:
`POST /runs` triggers scraping work via FastAPI background tasks and marks run state through `running -> scraping -> completed|completed_with_errors` without adding external queue infrastructure yet.

Reason:
Implements required Phase 2 behavior with minimal architecture overhead, consistent with MVP-first and explicit-flow constraints.

---

## 2026-05-25
Decision:
Phase 3 adds explicit provider modules (`gemini_client.py`, `hunter_client.py`) and routes all dossier/enrichment execution through `RunService` with validated provider outputs.

Reason:
Preserves architecture boundaries (routes thin, integrations isolated) while making third-party response handling explicit and testable.

---

## 2026-05-25
Decision:
When Hunter lookup fails, company rows remain `pending_review` and provider failure details are persisted in company metadata; run-level `error_message` stores non-fatal failure summaries.

Reason:
Keeps companies reviewable even when enrichment is incomplete, while surfacing recoverable provider issues to polling clients.

---

## 2026-05-25
Decision:
Phase 4 introduces explicit company review endpoints (`GET /runs/{run_id}/companies`, `PATCH /companies/{company_id}`, `GET /runs/{run_id}/companies/pending-count`) through a dedicated `CompanyService` ownership and transition guard layer.

Reason:
Keeps review behavior aligned with API contracts while preserving route thinness and server-side ownership enforcement.

---

## 2026-05-25
Decision:
Company status updates are restricted to review states (`pending_review`, `accepted`, `rejected`) and reject transitions from failure states.

Reason:
Prevents ambiguous lifecycle mutations and preserves explicit failure semantics for `dossier_failed`/`scrape_failed` records.

---

## 2026-05-29
Decision:
Phase 4 frontend is scaffolded under `/frontend` as a minimal Next.js app with a dedicated review dashboard wired to `GET /runs/{run_id}/companies`, `PATCH /companies/{company_id}`, and `GET /runs/{run_id}/companies/pending-count`.

Reason:
Closes the remaining Phase 4 wiring gap with explicit client-side state flow and test coverage for swipe-triggered API calls.

---

## 2026-05-30
Decision:
Phase 5 message generation is implemented as a dedicated backend service (`OutreachGenerationService`) behind `POST /runs/{run_id}/generate-messages`, with run-ownership checks, run-state guardrails, accepted-company filtering, and per-user daily generation quota enforcement.

Reason:
Keeps route handlers thin while enforcing server-side controls for generation eligibility and quota safety.

---

## 2026-05-30
Decision:
Generation failures now persist explicit `outreach` rows with `status=\"generation_failed\"` and `error_message`, while successful generations persist `status=\"draft\"`; run state advances through `messages_generating -> messages_generated`.

Reason:
Preserves debuggability and lifecycle clarity without dropping failed attempts.
