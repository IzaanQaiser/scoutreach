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
