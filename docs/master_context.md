# MASTER_CONTEXT.md

# ScoutReach Master Context

This document is the primary entrypoint for AI coding agents and developers working on ScoutReach.

Before making any changes:
- read this document fully
- follow all linked documentation
- preserve system invariants
- preserve architecture unless explicitly instructed otherwise

This file defines:
- project purpose
- architectural philosophy
- required reading order
- documentation responsibilities
- update rules
- engineering constraints

---

# What Is ScoutReach

ScoutReach is an AI-powered founder outreach platform that helps users:
- discover YC startups
- evaluate startup matches using a Tinder-style swipe flow
- generate personalized founder outreach using AI
- review/edit outreach drafts
- send approved outreach through Gmail integrations

The system:
- scrapes YC startup/company data
- enriches startup information
- generates structured company dossiers
- matches companies against user preferences
- generates personalized outreach drafts

Current status:
- MVP / public beta

---

# Core Product Philosophy

ScoutReach prioritizes:
- fast iteration
- lean architecture
- simplicity
- explicit systems
- debuggability
- maintainability

ScoutReach intentionally avoids:
- premature optimization
- overengineering
- speculative infrastructure
- unnecessary abstractions

---

# Required Reading Order

AI coding agents MUST read documents in this order before implementing changes.

## 1. Product + Scope

### `/docs/brief.md`
Purpose:
- high-level product overview
- MVP goals
- core product direction

### `/docs/mvp_scope.md`
Purpose:
- defines what IS in MVP
- defines what is explicitly OUT of MVP
- prevents scope creep

---

## 2. Architecture

### `/docs/architecture.md`
Purpose:
- system architecture
- sequence diagrams
- user flows
- data flow
- integrations
- orchestration logic

### `/docs/db_schema.md`
Purpose:
- database structure
- entity relationships
- statuses
- ownership model

### `/docs/api_contracts.md`
Purpose:
- backend endpoints
- request/response expectations
- frontend/backend contracts

---

## 3. Engineering Rules

### `/docs/development_standards.md`
Purpose:
- coding standards
- architecture rules
- repo organization
- error handling standards
- logging standards
- dependency rules

This document defines HOW code should be written.

### `/docs/system_invariants.md`
Purpose:
- defines architectural truths that must NEVER break
- defines ownership guarantees
- defines lifecycle guarantees
- defines sending and review guarantees

This document defines WHAT must always remain true.

---

## 4. Operational Docs

### `/docs/commands.md`
Purpose:
- development commands
- testing commands
- local environment commands

### `/docs/testing.md`
Purpose:
- testing expectations
- required test coverage
- validation requirements

### `/docs/git_workflow.md`
Purpose:
- commit conventions
- branch naming
- PR standards

---

## 5. Long-Term Repo Memory

### `/docs/decisions.md`
Purpose:
- architecture decisions
- reasoning behind important implementation choices

MUST be updated whenever:
- architecture changes
- major tradeoffs are made
- important constraints are introduced

---

### `/docs/known_gaps.md`
Purpose:
- tracks technical debt
- temporary compromises
- future improvements
- incomplete systems

MUST be updated whenever:
- shortcuts are taken
- temporary implementations are added
- missing functionality is discovered

---

# AI Agent Operating Rules

## Scope Discipline

Implement ONLY the requested scope.

Do NOT:
- redesign architecture
- add speculative systems
- add new infrastructure
- add unrelated features

unless explicitly requested.

---

## Dependency Discipline

Do NOT add dependencies unless:
- required for core functionality
- actively maintained
- significantly simplify implementation
- no lightweight alternative exists

---

## Refactor Discipline

Do NOT refactor working systems unless:
- bug exists
- architecture is blocked
- duplication is severe
- explicitly instructed

---

## Documentation Discipline

If architecture or behavior changes:
- update relevant docs
- update diagrams if necessary
- update decisions.md
- update known_gaps.md if needed

Documentation is part of the codebase.

---

# Required Post-Task Output

After completing a task, AI agents should summarize:

## Files Changed
- list modified files

## What Was Implemented
- concise implementation summary

## Architectural Impact
- whether architecture changed

## New Dependencies
- list added dependencies and justification

## Tests
- tests added
- tests run

## Documentation Updates
- docs updated

## Known Gaps Introduced
- temporary compromises
- TODOs
- limitations

---

# Core Architectural Principles

ScoutReach should remain:
- understandable by one engineer
- easy to debug
- easy to iterate on
- resistant to bloat
- explicit instead of magical

Prefer:
- simple code
- explicit flow
- boring architecture

over:
- clever abstractions
- unnecessary patterns
- premature scalability systems

---

# Final Rule

If implementation uncertainty exists:
- make the safest minimal assumption
- preserve architecture
- leave a TODO
- document uncertainty clearly

Do NOT invent speculative systems.