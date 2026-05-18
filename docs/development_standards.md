# DEVELOPMENT_STANDARDS.md

## Purpose

This document defines the engineering standards, architectural constraints, coding conventions, and operational expectations for ScoutReach.

The primary goals are:

- Maintain a lean and understandable codebase
- Prevent architectural drift and unnecessary abstraction
- Keep development velocity high
- Ensure AI coding agents work consistently and safely
- Optimize for fast iteration during MVP and beta stages
- Reduce technical debt accumulation

The codebase should prioritize:
- clarity
- explicitness
- maintainability
- predictable behavior
over premature optimization or overengineering.

---

# Core Engineering Philosophy

## Build the Simplest Thing That Works

Do not build speculative infrastructure.

Do not add systems "for future scaling" unless:
- the current architecture is blocked
- there is measured pain
- the feature is actively being implemented

Avoid:
- microservices
- event buses
- generic framework layers
- plugin systems
- unnecessary abstraction
- premature caching
- unnecessary background workers

Prefer:
- direct logic
- explicit data flow
- understandable APIs
- boring architecture

---

# MVP Philosophy

ScoutReach is currently an MVP/public beta product.

Development should optimize for:
- speed
- iteration
- correctness
- visibility
- debuggability

NOT:
- perfect scalability
- enterprise-grade complexity
- advanced optimization

---

# Repository Structure

## Backend Structure

```text
/backend
    /app
        /api
        /services
        /db
        /models
        /schemas
        /integrations
        /utils
        /middleware
        /jobs
````

### Responsibilities

#### `/api`

Route handlers only.
No business logic.

#### `/services`

Core application/business logic.

Examples:

* run_service.py
* outreach_service.py
* generation_service.py

#### `/db`

Database access and queries.

#### `/models`

ORM/database models.

#### `/schemas`

Pydantic request/response schemas.

#### `/integrations`

External APIs and providers.

Examples:

* gemini_client.py
* gmail_client.py
* hunter_client.py
* playwright_scraper.py

#### `/utils`

Pure helper functions only.

#### `/middleware`

Authentication, rate limiting, request logging.

#### `/jobs`

Long-running async tasks.

---

## Frontend Structure

```text
/frontend
    /app
    /components
    /lib
    /hooks
    /services
    /types
    /styles
```

---

# Architectural Rules

## Business Logic Must Not Live in Routes

BAD:

```python
@app.post("/runs")
def create_run():
    # 200 lines of logic
```

GOOD:

```python
@app.post("/runs")
def create_run():
    return run_service.create_run()
```

---

## External API Logic Must Be Isolated

All third-party integrations must live inside `/integrations`.

Never scatter:

* Gemini calls
* Gmail calls
* Hunter calls
* Playwright logic

throughout the codebase.

---

## Database Queries Must Be Centralized

Avoid inline raw queries across services.

Prefer:

```python
run_repository.create()
company_repository.update_status()
```

---

## One Responsibility Per Module

Files should do one thing well.

BAD:

```text
generation_service.py
- generates messages
- sends emails
- updates DB
- validates auth
- scrapes websites
```

GOOD:

```text
generation_service.py
email_service.py
scraper_service.py
```

---

# File Size Rules

## Backend

Preferred:

* under 300 lines per file

Warning:

* over 500 lines

Hard limit:

* 800+ lines requires refactor

---

## Frontend Components

Preferred:

* under 200 lines per component

If component becomes large:

* extract hooks
* extract subcomponents
* extract utility functions

---

# Naming Conventions

## Python

### Files

```text
snake_case.py
```

### Variables

```python
run_id
company_status
```

### Classes

```python
RunService
OutreachGenerator
```

---

## TypeScript

### Components

```text
PascalCase.tsx
```

### Hooks

```text
useRunPolling.ts
```

### Utilities

```text
formatDate.ts
```

---

# Database Standards

## UUIDs Everywhere

All primary IDs should use UUIDs.

Never use incremental integer IDs for public-facing entities.

---

## Timestamps

Every major table must include:

```text
created_at
updated_at
```

Important lifecycle tables should also include:

```text
completed_at
sent_at
started_at
```

---

## Status Fields

All status fields must use explicit enums/constants.

Never use arbitrary strings across the app.

BAD:

```python
status = "done"
status = "completed"
status = "finished"
```

GOOD:

```python
RUN_STATUS_COMPLETED
```

---

## Avoid Over-Normalization

For MVP:

* JSONB is acceptable
* denormalized storage is acceptable

Optimization can happen later.

---

# Error Handling Standards

## Never Swallow Errors

BAD:

```python
except:
    pass
```

GOOD:

```python
except Exception as e:
    logger.error(...)
    raise
```

---

## External API Failures Must Be Handled

Every external provider call must:

* handle timeouts
* handle rate limits
* handle malformed responses
* return structured errors

---

## Runs Must Never Silently Die

If a run fails:

* update DB status
* store error_message
* surface failure to frontend

---

# Logging Standards

## Log Important State Changes

Required logs:

* run created
* scrape started
* scrape completed
* generation started
* email send success/failure
* regeneration events
* quota violations
* external API failures

---

## Structured Logging

Prefer:

```python
logger.info(
    "run_created",
    run_id=run_id,
    user_id=user_id
)
```

Avoid vague logs:

```python
logger.info("something happened")
```

---

# Rate Limiting Standards

All public endpoints must support rate limiting.

Required protected operations:

* creating runs
* generating messages
* regenerating drafts
* sending emails

---

# Environment Variable Rules

## Never Hardcode Secrets

Use `.env`.

Never commit:

* API keys
* secrets
* tokens
* passwords

---

## Required Variables Must Be Validated on Startup

Backend should fail loudly if required env vars are missing.

---

# Frontend Standards

## Keep State Minimal

Avoid giant global state systems unless necessary.

Prefer:

* local state
* React Query
* simple hooks

before adding:

* Redux
* Zustand
* MobX

---

## Avoid Premature UI Abstraction

Do not create reusable abstractions unless reused multiple times.

---

## Loading and Error States Are Required

Every async UI flow must have:

* loading state
* error state
* empty state

---

# AI Generation Standards

## AI Output Must Never Be Trusted Blindly

All generated content must:

* be reviewable
* be editable
* be storable
* support regeneration

---

## Preserve Context

Generation requests should use:

* profile snapshot
* company dossier
* message preferences
* prior review context

---

## Generation Must Be Deterministic Enough for Debugging

Store:

* prompts
* metadata
* rationale when useful

---

# Sending Standards

## Public MVP Requires Manual Review

Auto-send should NOT be default public behavior.

Users must review generated outreach before sending.

---

## Sending Must Be Traceable

Every send attempt must store:

* timestamp
* result
* failure reason if applicable

---

# Git Standards

## Small Commits

Prefer:

* isolated commits
* focused changes

Avoid:

* giant mixed commits

---

## Branch Naming

```text
feature/run-generation
fix/gmail-failure-handling
refactor/outreach-service
```

---

# Documentation Standards

When architecture changes:

* update diagrams
* update DB schema docs
* update API contracts

Documentation is part of the codebase.

---

# AI Agent Standards

AI coding agents must:

* implement only requested scope
* avoid speculative refactors
* avoid dependency sprawl
* preserve architecture
* explain major decisions
* summarize modified files
* leave TODOs instead of inventing assumptions

---

# Performance Philosophy

Do not optimize early.

Only optimize when:

* measured bottlenecks exist
* users are impacted
* costs become significant

Correctness and iteration speed matter more than micro-optimizations during MVP.

---

# Security Standards

Never trust frontend input.

Validate:

* auth
* ownership
* quotas
* status transitions

on backend.

---

# Final Principle

ScoutReach should remain:

* understandable by a single engineer
* fast to iterate on
* easy to debug
* resistant to architectural bloat

Every engineering decision should favor:

* simplicity
* clarity
* speed of iteration
* maintainability
  over complexity or theoretical scalability.

  Follow commit and PR standards defined in /docs/GIT_WORKFLOW.md