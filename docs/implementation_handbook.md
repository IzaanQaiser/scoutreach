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

