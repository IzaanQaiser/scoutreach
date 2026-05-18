# ScoutReach — Codex Rules & Engineering Standards

This document defines the operating rules, engineering standards, architectural boundaries, and workflow expectations for AI coding agents working on ScoutReach.

The goal is to:
- keep the repository lean
- prevent architectural drift
- reduce unnecessary complexity
- maintain consistency across sessions
- prioritize shipping a reliable MVP quickly

This file is mandatory reading before making changes.

---

# 1. Project Overview

ScoutReach is an AI-powered founder outreach platform that helps users:
- discover YC startups
- evaluate companies through a Tinder-style matching flow
- generate personalized founder outreach using AI
- review/edit outreach drafts
- send approved outreach messages

Core stack:
- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: Supabase Postgres
- Scraping: Playwright
- AI generation: Gemini
- Email sending: Gmail API
- Email enrichment: Hunter.io

The product is currently an MVP-focused public beta.

---

# 2. Primary Engineering Philosophy

## PRIORITY ORDER

Always optimize for:

1. Correctness
2. Simplicity
3. Readability
4. Maintainability
5. Speed of implementation
6. Performance optimization

Do NOT prematurely optimize.

---

# 3. MVP Philosophy

This repository is MVP-first.

The objective is:
- ship quickly
- validate usage
- collect feedback
- iterate from real-world usage

Do NOT:
- build enterprise infrastructure prematurely
- over-engineer abstractions
- add speculative features
- create unnecessary layers
- optimize hypothetical scale problems

---

# 4. Architectural Principles

## Backend responsibilities
FastAPI orchestrates:
- runs
- scraping
- generation
- outreach workflows
- rate limiting
- permissions
- persistence

## Scraper responsibilities
Playwright handles:
- YC scraping
- company website scraping
- raw content extraction

Scrapers should NOT:
- generate business logic
- generate AI summaries
- make product decisions

## Gemini responsibilities
Gemini handles:
- company understanding
- dossier generation
- outreach generation
- message regeneration

Gemini outputs should ALWAYS be validated and persisted by backend logic.

## Database responsibilities
Supabase stores:
- user state
- runs
- companies
- outreach drafts
- statuses
- history

Database should remain the source of truth.

## Frontend responsibilities
Frontend handles:
- UI
- polling
- interactions
- local optimistic state

Frontend should NOT:
- contain business logic
- contain authorization logic
- contain generation logic

---

# 5. Repository Standards

## Keep files small
Target:
- <300 lines preferred
- <500 lines maximum unless justified

If a file becomes too large:
- split by responsibility
- avoid giant utility files

---

## Keep functions focused
Functions should:
- do one thing
- be easy to test
- have clear inputs/outputs

Avoid:
- giant multi-purpose functions
- deeply nested logic

---

## Avoid premature abstractions

DO NOT:
- build frameworks
- create generic engines prematurely
- abstract for hypothetical future use

Prefer:
- explicit code
- direct implementations
- boring architecture

Duplicate small amounts of code if abstraction would reduce clarity.

---

# 6. Dependency Rules

## Before adding a dependency

The agent MUST ask:
- is this already solvable with current stack?
- is this dependency actively maintained?
- is this dependency lightweight?
- is this dependency worth long-term maintenance cost?

Avoid:
- large frameworks
- unnecessary wrappers
- dependencies for trivial utilities

Prefer:
- standard library
- lightweight packages
- direct implementations

---

# 7. Database Rules

## Database migrations
All schema changes MUST:
- use migrations
- be reversible
- preserve existing data

Never:
- mutate production tables manually
- silently rename/drop columns

---

## Status fields
Statuses must remain explicit.

Avoid:
- magic strings scattered everywhere

Prefer:
- centralized enums/constants

Example:
- running
- completed
- failed
- pending_review
- accepted
- rejected
- draft
- approved
- sent
- failed

---

## Snapshots
Runs use profile snapshots intentionally.

Do NOT:
- replace snapshots with live profile reads

Reason:
- runs must remain historically reproducible

---

# 8. API Standards

## API design philosophy

Endpoints should:
- be explicit
- predictable
- REST-like
- simple

Avoid:
- overloaded endpoints
- hidden behavior
- implicit side effects

---

## API responses

Responses should:
- be typed
- consistent
- serializable
- stable

Errors should:
- return actionable messages
- never expose secrets
- include machine-readable status codes

---

## Validation
ALL input must be validated:
- request body
- query params
- IDs
- enums
- limits

Never trust frontend input.

---

# 9. Error Handling Rules

## All external services can fail

Always assume:
- Playwright can fail
- Gemini can timeout
- Gmail can fail
- Hunter can fail
- Supabase can fail

All external calls must:
- be wrapped
- log failures
- preserve recoverability

---

## Never crash runs unnecessarily

If one company fails:
- continue the run
- log the failure
- preserve partial progress

Only fail entire runs for catastrophic failures.

---

## Preserve failure visibility

Failures must:
- update DB status
- include error_message
- remain inspectable later

Never swallow errors silently.

---

# 10. Logging Standards

All important workflows should log:
- run creation
- scraper start/failure
- generation failure
- email sending
- quota violations
- regeneration events

Logs should include:
- run_id
- company_id when relevant
- outreach_id when relevant
- timestamps
- failure reasons

Avoid:
- noisy logs
- logging secrets
- logging raw tokens/credentials

---

# 11. Rate Limiting & Abuse Prevention

Public MVP MUST enforce:
- run quotas
- generation quotas
- regeneration quotas
- sending quotas

Do NOT:
- allow infinite AI usage
- allow uncontrolled sending

All limits should be configurable.

---

# 12. AI Generation Rules

## AI output is untrusted
Never assume:
- Gemini output is valid
- formatting is correct
- emails are safe

Always:
- validate outputs
- sanitize content
- persist safely

---

## Keep prompts centralized
Prompts should:
- live in dedicated prompt files
- be versionable
- be editable without touching business logic

Do NOT:
- inline giant prompts across the codebase

---

# 13. Email Rules

## Public MVP defaults
Manual review is REQUIRED by default.

Auto-send should:
- remain disabled by default
- require explicit enablement
- respect quotas

---

## Sending rules
Never:
- send duplicate emails accidentally
- send without status tracking
- send without persistence

Every send attempt must:
- update DB state
- store timestamps
- store failures

---

# 14. Frontend Rules

## UI philosophy
UI should feel:
- minimal
- fast
- smooth
- obvious
- low-friction

Avoid:
- clutter
- heavy animations
- enterprise-looking dashboards

---

## Frontend state
Prefer:
- server truth
- polling
- simple local state

Avoid:
- unnecessary global state systems
- overcomplicated caching

---

# 15. Security Rules

Never:
- expose API keys
- expose secrets to frontend
- trust client-side permissions

All secrets:
- stay server-side
- use env vars
- use .env.example

---

# 16. Environment Variables

All required env vars must:
- be documented
- exist in .env.example

Never:
- hardcode credentials
- hardcode secrets
- hardcode production URLs

---

# 17. Git & Commit Standards

## Keep commits focused
Each commit should:
- solve one problem
- implement one feature
- be reviewable

Avoid:
- giant mixed commits
- unrelated refactors

---

## Commit message style

Use:
- feat:
- fix:
- refactor:
- docs:
- chore:

Examples:
- feat: implement run creation endpoint
- fix: handle hunter timeout failures
- refactor: split outreach generation service

---

# 18. Testing Standards

Critical flows must eventually have tests:
- run creation
- scraping pipeline
- outreach generation
- approval flow
- sending flow

Prefer:
- integration tests for pipelines
- unit tests for utility logic

Avoid:
- brittle UI snapshot tests

---

# 19. Refactoring Rules

Do NOT refactor:
- unrelated code
- entire systems
- architecture

unless explicitly requested.

Prefer:
- local improvements
- incremental cleanup
- preserving working behavior

---

# 20. Documentation Rules

When architecture changes:
- update docs
- update diagrams if needed
- update API contracts if affected

Documentation should remain aligned with reality.

---

# 21. Codex Workflow Rules

For every implementation task:

1. Read relevant docs first
2. Create a brief implementation plan
3. Implement smallest working version
4. Validate behavior
5. Summarize changes

Do NOT:
- invent new architecture
- silently add dependencies
- silently change workflows

---

# 22. If Unclear

If requirements are ambiguous:
- make the safest minimal assumption
- leave TODO notes where necessary
- avoid speculative implementation

Prefer:
- shipping working software
over
- building theoretical perfection

---

# 23. Forbidden Behaviors

NEVER:
- rewrite large sections unnecessarily
- add frameworks without approval
- delete working functionality
- silently change DB schemas
- silently change API contracts
- silently change auth logic
- expose secrets
- bypass validation
- bypass quotas
- create massive files
- create dead abstractions
- optimize prematurely

---

# 24. Success Criteria

Good code in this repo is:
- understandable
- explicit
- stable
- testable
- easy to debug
- easy to extend
- lean
- fast to iterate on

The best solution is usually the simplest one that works reliably.
