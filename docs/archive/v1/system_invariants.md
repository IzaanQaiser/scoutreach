# SYSTEM_INVARIANTS.md

# Purpose

This document defines the core system invariants for ScoutReach.

System invariants are architectural truths and safety guarantees that should always remain valid across:
- backend logic
- frontend behavior
- database operations
- AI agent modifications
- future refactors

If an invariant must change:
- the architecture must be intentionally redesigned
- docs must be updated
- dependent systems must be audited

These are NOT suggestions.

---

# Core Ownership Invariants

## Every run must belong to exactly one user

- `runs.user_id` must always reference a valid user
- orphaned runs are invalid
- runs must never be globally accessible

---

## Every company must belong to exactly one run

- `companies.run_id` is required
- companies cannot exist independently
- deleting a run should handle company cleanup safely

---

## Every outreach row must belong to:
- exactly one user
- exactly one run
- exactly one company

Required fields:
- `user_id`
- `run_id`
- `company_id`

Orphaned outreach rows are invalid.

---

# Authorization Invariants

## Users may only access their own data

A user must never access:
- another user's runs
- another user's companies
- another user's outreach rows
- another user's drafts
- another user's profile snapshot

Ownership validation must happen on the backend.

Frontend restrictions alone are NOT sufficient.

---

## Backend is the source of truth

The frontend must never be trusted for:
- ownership
- permissions
- quotas
- status transitions
- sending authorization

All validations must occur server-side.

---

# Outreach Invariants

## Outreach messages must remain editable

Generated messages are suggestions.

Users must always be able to:
- edit subject
- edit message body
- regenerate
- reject
- approve manually

Generated AI output is never final by default.

---

## Public MVP requires manual review before sending

Public beta behavior must require:
- message review
- explicit approval
- intentional send action

Mass autonomous sending is not allowed in public MVP.

---

## Outreach sending requires approved status

Only outreach rows with:
```text
status = "approved"
````

may be sent.

Drafts, failed rows, rejected rows, and needs_review rows must never bypass approval flow.

---

## Failed sends must preserve failure state

If sending fails:

* preserve error_message
* preserve failed status
* preserve original message content
* preserve timestamps

Failed sends must remain debuggable.

---

# Run Lifecycle Invariants

## Runs must always have a valid lifecycle state

Allowed statuses:

```text
running
failed
completed
messages_generated
```

Invalid arbitrary statuses must not exist.

---

## Runs must surface failures explicitly

Runs may never silently fail.

If a major failure occurs:

* update status
* store error_message
* expose failure to frontend polling

---

## Run progress must remain bounded

Progress must always be:

```text
0 <= progress <= 100
```

---

# Company Invariants

## Company review state must be explicit

Allowed company states:

```text
pending_review
accepted
rejected
dossier_failed
```

---

## Scraped raw data must be preserved

Original scraped content should not be overwritten destructively.

The system should preserve:

* raw scrape
* generated dossier
* enrichment metadata

This allows:

* debugging
* regeneration
* future model improvements

---

## Companies may exist without verified emails

Hunter failures must not invalidate companies.

A company may still:

* appear in swipe flow
* be reviewed
* generate drafts

even if no verified founder email exists.

---

# AI Generation Invariants

## AI generations must remain reproducible enough for debugging

The system should preserve:

* generation context
* prompts or prompt metadata when practical
* profile snapshot
* company dossier

This enables:

* debugging
* regeneration
* quality analysis

---

## Profile snapshot must remain immutable per run

Runs should preserve a snapshot of:

* candidate profile
* message preferences
* target roles

Changes to the live user profile should not retroactively alter historical runs.

---

## Regeneration must preserve history safely

Regeneration must never:

* corrupt unrelated drafts
* break ownership relationships
* remove send history

---

# Database Invariants

## UUIDs are the canonical identifiers

Primary entities must use UUIDs:

* users
* runs
* companies
* outreach

Public APIs should never depend on sequential IDs.

---

## Timestamps are required for major entities

All major entities must preserve:

* created_at
* updated_at

Lifecycle entities should additionally preserve:

* sent_at
* started_at
* completed_at

---

# Rate Limiting Invariants

## Quotas must be enforced server-side

Critical operations requiring quotas:

* creating runs
* generating messages
* regenerating drafts
* sending outreach

Frontend-only enforcement is invalid.

---

## Quota failures must not partially mutate state

If quota validation fails:

* no partial send should occur
* no partial generation should occur
* no inconsistent DB state should remain

---

# External API Invariants

## External provider failures must not crash the system

Failures from:

* Gemini
* Hunter
* Gmail
* Playwright

must be:

* isolated
* logged
* recoverable when possible

---

## Third-party responses are untrusted

Always validate:

* structure
* required fields
* types
* emptiness

before persisting or using external API responses.

---

# Logging Invariants

## Important state transitions must be logged

Required logging events:

* run creation
* scrape start
* scrape failure
* dossier generation failure
* outreach generation
* send success
* send failure
* quota rejection

---

# Refactor Invariants

## Working flows should not be rewritten without reason

Do not refactor stable systems unless:

* bug exists
* architecture is blocked
* duplication is severe
* explicitly requested

---

# Final Principle

ScoutReach must remain:

* understandable
* debuggable
* recoverable
* user-controlled
* safe for public beta usage

No optimization, abstraction, or AI-generated change should violate these invariants.