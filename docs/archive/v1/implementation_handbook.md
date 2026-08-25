# IMPLEMENTATION_HANDBOOK.md

# ScoutReach Implementation Handbook

This is the single-link operating handbook for implementation work on ScoutReach.

Use this when you want one document that captures:
- development principles
- code and architecture standards
- testing standards
- git/commit/PR standards
- delivery and documentation expectations

This document consolidates existing rules. It does not replace core source docs.

Primary source docs:
- `/agents.md`
- `/docs/master_context.md`
- `/docs/system_invariants.md`
- `/docs/development_standards.md`
- `/docs/codex_rules.md`
- `/docs/git_workflow.md`
- `/docs/testing.md`

---

# 1. Working Agreement

Before implementation:
1. Read `/docs/master_context.md`
2. Read `/agents.md`
3. Read relevant product/architecture/contract docs for the requested phase

Default behavior:
- implement only requested scope
- preserve existing behavior unless explicitly asked to change it
- keep MVP lean and explicit
- avoid speculative architecture and infrastructure

If unclear:
- make the safest minimal assumption
- leave a TODO
- document the uncertainty in task output

---

# 2. Project Context (Execution Lens)

ScoutReach is an MVP/public-beta outreach workflow product.

Core direction:
- speed of iteration
- reliability and debuggability
- user-controlled outbound messaging
- manual review before sending in public MVP

Not the goal right now:
- enterprise-scale abstractions
- autonomous mass outbound
- speculative future platform systems

---

# 3. Architecture Guardrails

System roles:
- Frontend (Next.js): UI, interaction, polling, local state
- Backend (FastAPI): orchestration, authz, quotas, provider calls, persistence
- Database (Supabase): source of truth for user/run/company/outreach state
- Providers: Playwright (scrape), Gemini (generation), Hunter (enrichment), Gmail (send)

Hard boundaries:
- frontend does not call providers directly
- business logic does not live in API route handlers
- third-party provider logic lives under integrations
- DB access/query patterns stay centralized

One-responsibility rule:
- prefer small focused modules and explicit flow over multi-purpose files

---

# 4. Non-Negotiable Invariants

Do not violate:
- ownership and auth invariants
- server-side validation and authorization
- manual-review-first public sending behavior
- approved-only send rule
- explicit failure state persistence
- immutable per-run profile snapshot behavior
- quota enforcement server-side

When touching affected flows, review:
- `/docs/system_invariants.md`

---

# 5. Coding Standards

Code style goals:
- correctness first
- simplicity over cleverness
- readability and maintainability
- explicit boring code

Repository structure expectations:
- route handlers thin
- services hold business logic
- integrations isolate third-party APIs
- middleware handles auth/rate limiting/logging

Naming:
- Python files and variables: snake_case
- TypeScript components: PascalCase
- hooks: useX naming

File size guidance:
- backend files: prefer <300 lines, warn >500
- frontend components: prefer <200 lines

Avoid:
- giant generic utility layers
- premature abstraction/frameworking
- dependency sprawl

---

# 6. Dependency and Refactor Policy

Before adding a dependency:
- confirm current stack cannot solve cleanly
- verify active maintenance
- verify real complexity reduction
- justify long-term maintenance cost

Do not refactor working code unless:
- there is a bug
- architecture is blocked
- duplication is severe
- task explicitly asks for refactor

No silent system redesigns.

---

# 7. API and Data Contract Discipline

API rules:
- explicit, predictable, stable endpoint behavior
- typed and consistent response formats
- actionable machine-readable errors
- strict validation of body/query/IDs/enums/limits

Data rules:
- preserve ownership relationships
- use explicit status constants/enums in code
- do not break contract fields without explicit scope
- avoid destructive schema behavior
- use migrations for schema changes

---

# 8. Public-Release Limit Safety (Required)

For sending, generation, and enrichment flows:
- use async jobs for bulk operations
- do not fan out synchronously from a single request
- enforce layered throttling:
  - per-user
  - per-provider
  - per-operation
- use bounded concurrency
- use exponential backoff with jitter for 429/5xx/timeouts
- enforce idempotency for outbound sends
- ensure fairness so one heavy user cannot starve others

No public release of high-volume outbound flows without these controls.

---

# 9. Error Handling and Logging

Error handling:
- never swallow exceptions
- isolate provider failures
- preserve recoverability
- persist clear error_message and state transitions

Logging:
- log meaningful workflow transitions only
- include identifiers (`run_id`, `company_id`, `outreach_id`) when relevant
- avoid noisy logs and secret leakage

---

# 10. Testing Standards

Prioritize critical path tests:
- run creation and ownership
- scrape/storage behavior
- company review status transitions
- outreach generation and review
- send-approved flow
- failure handling and quota enforcement

Testing structure:
- backend unit + integration first
- mock external providers in normal test runs
- keep tests high-signal and behavior-focused

Use:
- `/docs/testing.md`
- `/docs/commands.md`

---

# 11. Git, Commit, and PR Standards

Branch naming:
- `feature/<short-description>`
- `fix/<short-description>`
- `refactor/<short-description>`
- `docs/<short-description>`

Commit style:
- one logical change per commit
- explicit prefix: `feat|fix|refactor|docs|chore|test`
- concise present-tense subject line

PR scope:
- one feature, bug, refactor, or doc concern per PR
- avoid mixed unrelated changes

Use:
- `/docs/git_workflow.md`

---

# 12. Documentation Update Rules

When behavior/architecture/contracts change:
- update affected docs in same change
- update decisions/gaps docs when applicable
- keep markdown map in `/docs/master_context.md` current

If a shortcut or temporary compromise is introduced:
- add a clear note to `/docs/known_gaps.md`

---

# 13. Task Completion Output (Required)

After implementation, always include:
- files changed
- what was implemented
- architectural impact
- dependencies added (with justification)
- tests added/run
- docs updated
- known gaps/TODOs introduced

Use `/docs/task_template.md` for consistent output shape.

---

# 14. Conflict Resolution

If docs appear to conflict, follow precedence in:
- `/docs/master_context.md` ("Document Precedence")

Practical rule:
- preserve invariants
- make safest minimal assumption
- leave TODO and call out conflict in summary

---

# 15. Phased Implementation Checklist (Strict Gates)

Use this as the execution plan. Do not move to the next phase until the current phase is fully green.

Global gate for every phase:
- implement only that phase scope
- preserve existing behavior
- keep statuses/contracts aligned with docs
- update docs when behavior/contracts change
- run required tests before phase sign-off

## Phase 1: Foundations

Scope:
- repo/app skeleton readiness
- FastAPI app shell
- Supabase connection setup
- authentication baseline
- DB schema/migrations for core tables

Acceptance criteria:
- backend starts cleanly and `/health` returns success
- core tables exist (`users`, `candidate_profile`, `runs`, `companies`, `outreach`)
- auth middleware exists and protects authenticated routes
- schema includes required ownership keys and timestamps

Done tests:
- backend smoke: server boot + health endpoint
- integration: authenticated request succeeds, unauthenticated request fails
- integration: migration creates required tables/constraints

## Phase 2: Runs + Scraping Persistence

Scope:
- create run flow
- run status polling flow
- scraper integration entrypoint
- company persistence per run

Acceptance criteria:
- `POST /runs` creates run with valid initial status/progress
- `GET /runs/{run_id}/status` returns current status/progress/error fields
- scraper output is normalized and stored under the correct `run_id`
- failed single-company scrape does not crash the full run

Done tests:
- integration: run creation under quota and rejection over quota
- integration: ownership checks for run reads
- integration: company rows persist with correct `run_id`
- integration: partial scrape failure preserves run continuity

## Phase 3: Dossier + Enrichment

Scope:
- Gemini dossier generation
- Hunter founder email enrichment
- persistence of success/failure metadata

Acceptance criteria:
- each persisted company has raw scrape plus dossier or explicit dossier failure state
- Hunter lookup results are stored on founder objects when available
- no-email/lookup-failure companies remain reviewable
- provider failures are logged and stored without collapsing the run

Done tests:
- unit: dossier parsing/validation logic
- integration: Gemini timeout/failure sets failure state correctly
- integration: Hunter empty/failure path still persists company as reviewable
- integration: provider error path stores error_message/log data

## Phase 4: Company Review (Swipe)

Scope:
- review queue retrieval
- accept/reject state updates
- pending count endpoint
- swipe UI wiring

Acceptance criteria:
- `GET /runs/{run_id}/companies?status=pending_review` returns review queue
- `PATCH /companies/{company_id}` supports allowed transitions
- `GET /runs/{run_id}/companies/pending-count` is accurate
- users cannot modify other users' company rows

Done tests:
- integration: pending queue returns only owned run data
- integration: accept/reject updates persist correctly
- integration: invalid transitions are rejected
- frontend behavior: swipe actions trigger correct API calls and state updates

## Phase 5: Outreach Generation

Scope:
- generate outreach for accepted companies
- draft persistence in `outreach`
- generation failure handling

Acceptance criteria:
- `POST /runs/{run_id}/generate-messages` enforces quota before generation
- draft outreach rows are created with correct ownership/run/company linkage
- generation failures create `generation_failed` rows with error context
- run status moves to messages-generated state after generation cycle

Done tests:
- integration: accepted-only companies are used for generation
- integration: generated drafts contain required fields/status
- integration: generation failure path persists `generation_failed`
- integration: ownership and quota checks block unauthorized/over-limit requests

## Phase 6: Review, Regenerate, Send

Scope:
- outreach review/update endpoints
- regenerate endpoint with critique
- send-approved flow via Gmail
- sent/failed state persistence

Acceptance criteria:
- users can edit/approve/reject/needs_review drafts they own
- regenerate keeps ownership/history safe and preserves prior draft on failure
- send flow only sends `approved` rows
- send results persist per-row success/failure and timestamps

Done tests:
- integration: `PATCH /outreach/{id}` allows only permitted states
- integration: regenerate success and failure paths behave correctly
- integration: send-approved enforces ownership, quota, and approved-only rule
- integration: Gmail failure marks row failed without crashing batch send

## Phase 7: Public Beta Hardening

Scope:
- rate-limit and quota hardening
- error handling polish and observability
- public-release safety controls
- final QA pass

Acceptance criteria:
- quotas enforced for run create, generation, regeneration, and send
- limit-safety protections exist for high-volume provider usage
- logs include critical state transitions and failure reasons
- public behavior keeps manual review before sending by default

Done tests:
- integration: quota rejection does not partially mutate send/generation state
- integration: retry/backoff/throttle behavior for simulated 429/5xx provider errors
- smoke: end-to-end happy path (start run -> review -> generate -> approve -> send)
- regression: key ownership and invariants still hold across core flows

## Phase Completion Protocol

To mark a phase complete:
- all phase acceptance criteria are true
- all phase done tests pass
- required docs are updated if behavior/contracts changed
- task output includes: files changed, implementation summary, tests run, and known gaps
