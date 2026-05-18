# GIT_WORKFLOW.md

# Purpose

This document defines the Git workflow, branching strategy, commit standards, pull request expectations, and repository hygiene rules for ScoutReach.

The goals are:
- maintain readable history
- keep AI-generated changes understandable
- reduce chaotic commits
- improve debugging and rollback safety
- prevent architecture drift
- keep collaboration clean and predictable

---

# Core Philosophy

Git history is part of the architecture.

Every commit should:
- communicate intent clearly
- be scoped narrowly
- be understandable weeks later
- be reversible safely

Avoid:
- giant mixed commits
- vague commit messages
- hidden refactors
- unrelated changes bundled together

---

# Branching Strategy

## Branch Types

### Feature Branches

Used for new functionality.

Format:
```text
feature/<short-description>
````

Examples:

```text
feature/run-generation
feature/swipe-ui
feature/gmail-sending
```

---

### Fix Branches

Used for bug fixes.

Format:

```text
fix/<short-description>
```

Examples:

```text
fix/run-status-polling
fix/generation-timeout
```

---

### Refactor Branches

Used for architecture or structural cleanup.

Format:

```text
refactor/<short-description>
```

Examples:

```text
refactor/outreach-service
refactor/db-repositories
```

---

### Documentation Branches

Used for docs-only changes.

Format:

```text
docs/<short-description>
```

Examples:

```text
docs/update-api-contracts
docs/add-known-gaps
```

---

# Commit Standards

## General Rules

Commits must:

* represent one logical change
* avoid mixing unrelated work
* be readable without opening the diff

---

## Commit Prefixes

### feat

New functionality.

Example:

```text
feat: implement run creation endpoint
```

---

### fix

Bug fixes.

Example:

```text
fix: prevent duplicate outreach generation
```

---

### refactor

Structural code improvements without behavior changes.

Example:

```text
refactor: extract gmail sending service
```

---

### docs

Documentation updates only.

Example:

```text
docs: update database schema notes
```

---

### chore

Maintenance tasks, configs, tooling.

Example:

```text
chore: add pre-commit formatting hooks
```

---

### test

Testing-related work.

Example:

```text
test: add outreach generation failure tests
```

---

# Commit Message Rules

## Keep Messages Explicit

BAD:

```text
fix stuff
updates
working now
cleanup
```

GOOD:

```text
fix: handle Hunter timeout failures
feat: add outreach regeneration endpoint
refactor: separate run status polling service
```

---

## Use Present Tense

GOOD:

```text
feat: add swipe review UI
```

BAD:

```text
feat: added swipe review UI
```

---

## Keep Subject Lines Short

Preferred:

* under 72 characters

---

# Pull Request Standards

## PR Scope

A PR should solve:

* one feature
* one bug
* one refactor
* one architectural concern

Avoid:

* giant "everything" PRs

---

## PR Naming

Format:

```text
[type] Short description
```

Examples:

```text
[feat] Add company swipe review flow
[fix] Handle failed Gmail sends
[refactor] Simplify outreach generation pipeline
```

---

# PR Description Template

Every PR should contain:

```md
# Summary
What changed?

# Why
Why was this needed?

# Files Changed
List major files/modules affected.

# Testing
What was tested?

# Notes
Anything reviewers or future developers should know.
```

---

# AI Agent Git Rules

AI coding agents must:

* avoid massive commits
* avoid unrelated edits
* avoid hidden refactors
* summarize all modified files
* explain architectural changes
* explain dependency additions
* explain schema changes

---

# Refactor Rules

## Do Not Refactor Working Code Without Reason

Allowed reasons:

* architecture blocked
* severe duplication
* major readability issue
* performance bottleneck
* explicitly requested

Not allowed:

* personal preference
* style preference
* speculative cleanup

---

# Dependency Change Rules

Any dependency addition must include:

* why it is needed
* alternatives considered
* expected long-term usage

Avoid dependency bloat.

---

# Database Migration Rules

Every schema change must:

* have a migration file
* update DB_SCHEMA.md
* preserve existing data when possible

Never silently modify production schema manually.

---

# Documentation Rules

When architecture changes:

* update diagrams
* update API contracts
* update DB schema docs
* update known gaps if relevant

---

# Testing Rules

Feature PRs should include:

* happy path coverage
* major failure path coverage

Fix PRs should include:

* regression protection when reasonable

---

# Main Branch Rules

The `main` branch should:

* remain deployable
* remain stable
* avoid experimental unfinished work

Never push unstable experimental code directly to main.

---

# Squashing

Squash commits before merge when:

* commit history is noisy
* WIP commits exist
* iterative AI-generated commits are messy

Preserve meaningful commit history when useful.

---

# Emergency Fixes

Critical production fixes may bypass normal workflow but must:

* be documented afterward
* include root cause notes
* update KNOWN_GAPS.md if applicable

---

# Final Principle

ScoutReach development should optimize for:

* clarity
* iteration speed
* maintainability
* debuggability
* controlled architecture evolution

Git history should help future development, not obscure it.