# TESTING.md

## Purpose

This document defines the testing standards for ScoutReach.

The goal is not to create a massive enterprise test suite. The goal is to make sure the MVP does not silently break while moving fast with AI-assisted development.

Tests should protect the core product flows:

- user creates a run
- scraper data is stored correctly
- company matching/swiping works
- messages are generated as drafts
- messages require review before sending
- approved messages can be sent
- failures are handled safely

---

# Testing Philosophy

## Test the Critical Path First

Prioritize tests for flows that affect:

- user data
- database writes
- external API calls
- email sending
- status transitions
- rate limits
- permissions

Do not over-test simple UI styling or basic rendering.

---

## Prefer Useful Tests Over Many Tests

A small number of strong tests is better than a huge weak test suite.

Every test should answer:

> If this fails, would we actually care?

If not, do not write the test yet.

---

# Test Types

ScoutReach should use four types of tests:

1. Backend unit tests
2. Backend integration tests
3. Frontend component tests
4. End-to-end smoke tests

For MVP, backend tests matter most.

---

# Backend Testing Standards

## Backend Test Location

Backend tests should live here:

```text
/backend/tests
````

Recommended structure:

```text
/backend/tests
    /unit
    /integration
    /fixtures
```

---

## Unit Tests

Unit tests should test isolated business logic.

Examples:

* status transition validation
* quota/rate-limit checks
* prompt payload construction
* message generation payload formatting
* company filtering logic
* ownership validation helpers

Unit tests should not call:

* Gemini
* Gmail
* Hunter
* live Supabase
* YC website

Use mocks/fakes.

---

## Integration Tests

Integration tests should test how app layers work together.

Examples:

* API endpoint creates correct DB rows
* accepted company gets updated correctly
* outreach draft is inserted correctly
* sending approved messages updates statuses correctly
* failed external provider response stores error_message

Integration tests may use:

* test database
* mocked external APIs
* FastAPI test client

Integration tests must not call real paid APIs during normal test runs.

---

# Frontend Testing Standards

## Frontend Test Location

Frontend tests should live near the relevant components or in:

```text
/frontend/tests
```

Recommended structure:

```text
/frontend/tests
    /components
    /flows
```

---

## Frontend Tests Should Cover

Only test frontend behavior that matters.

Examples:

* dashboard shows correct state for running run
* dashboard shows "Evaluate Matches" when run is completed
* swipe accept/reject triggers correct API request
* generated drafts show review controls
* send button only appears for approved messages
* loading, error, and empty states render correctly

Do not over-test:

* exact pixel layout
* Tailwind class names
* minor copy changes

---

# End-to-End Smoke Tests

E2E tests should validate the main happy path at a high level.

For MVP, one smoke test is enough:

1. user logs in or uses mocked auth
2. starts a run
3. run completes with mocked scraper data
4. user accepts one company
5. user generates a draft
6. user approves the draft
7. user sends approved message using mocked Gmail
8. dashboard shows result

E2E tests should use mocked external providers.

Do not rely on real YC, Gemini, Hunter, or Gmail for normal E2E runs.

---

# External API Testing Rules

External APIs must be mocked in normal tests.

Mock these providers:

* Gemini API
* Gmail API
* Hunter.io API
* Playwright YC scraper

Tests should simulate:

* success response
* timeout
* rate limit response
* malformed response
* empty response
* provider failure

---

# Required Backend Tests by Feature

## Runs

When implementing or changing run logic, tests must cover:

* user can create a run when under quota
* user cannot create a run when over quota
* run row is created with correct default status
* run progress can be updated
* run can be marked completed
* run can be marked failed with error_message
* user cannot access another user's run

---

## Scraping Pipeline

When implementing or changing scraper logic, tests must cover:

* scraper returns normalized company data
* failed company scrape does not crash entire run
* partial scraped data can be stored
* run progress updates after each company
* scraper failure updates run status or logs error
* duplicate companies in the same run are handled safely

---

## Company Matching / Swiping

When implementing or changing company matching logic, tests must cover:

* pending companies can be fetched for a run
* accepted company status updates correctly
* rejected company status updates correctly
* invalid status transitions are rejected
* user cannot update another user's company
* pending count returns correct value

---

## Message Generation

When implementing or changing message generation logic, tests must cover:

* only accepted companies are used for generation
* generation payload includes profile_snapshot
* generation payload includes job preferences
* generation payload includes message preferences
* generation payload includes company dossier
* generated subject and message_content are stored
* Gemini failure creates safe failure state
* generated messages start as draft, not sent

---

## Message Review

When implementing or changing review logic, tests must cover:

* draft can be approved
* draft can be edited
* draft can be marked needs_review
* draft can be regenerated
* failed regeneration preserves previous draft
* review summary counts statuses correctly
* user cannot review another user's outreach row

---

## Sending

When implementing or changing sending logic, tests must cover:

* only approved messages can be sent
* draft messages cannot be sent directly
* needs_review messages cannot be sent directly
* sent messages store sent_at
* Gmail failure stores error_message
* Gmail success updates status to sent
* user cannot send another user's outreach
* sending respects daily quota

---

## Rate Limiting

When implementing or changing rate limits, tests must cover:

* run creation quota
* message generation quota
* regeneration quota
* sending quota
* over-quota requests return clear errors
* quota checks happen before expensive provider calls

---

## Permissions / Ownership

Every endpoint that reads or writes user data must validate ownership.

Tests must cover:

* user can access their own runs
* user cannot access other users' runs
* user can access their own companies
* user cannot update other users' companies
* user can access their own outreach
* user cannot send other users' outreach

This is non-negotiable for public release.

---

# Required Frontend Tests by Feature

## Dashboard

Tests should cover:

* idle state
* running state
* failed state
* completed state
* messages generated state
* sent results state

---

## Match Evaluation UI

Tests should cover:

* company cards render
* accept action calls correct endpoint
* reject action calls correct endpoint
* empty queue shows generate messages CTA

---

## Message Review UI

Tests should cover:

* drafts render
* approve button works
* edit flow works
* regenerate action triggers correct endpoint
* needs_review/reject action works
* send approved button appears only when valid

---

# Minimum Test Requirements Before Public Beta

Before public beta, the repo must have tests for:

* run creation
* run status polling
* company accept/reject
* message generation creates drafts
* manual review required before sending
* approved messages can be sent
* failed sends store error_message
* ownership validation
* rate limits for run creation and sending

This is the public beta minimum.

---

# Test Data Rules

Use small, realistic fixtures.

Example company fixture:

```json
{
  "name": "ExampleAI",
  "yc_url": "https://www.ycombinator.com/companies/exampleai",
  "website_url": "https://example.ai",
  "domain": "example.ai",
  "batch": "S25",
  "founders": [
    {
      "name": "Aisha Khan",
      "linkedin_url": "https://linkedin.com/in/aishakhan",
      "email": "aisha@example.ai"
    }
  ],
  "tags": ["AI", "Developer Tools"],
  "dossier": {
    "summary": "ExampleAI helps developers automate code reviews.",
    "industry": "Developer Tools",
    "hiring_relevance": "Strong fit for full-stack and AI engineering outreach."
  }
}
```

Example candidate fixture:

```json
{
  "resume": "Software engineering student with React, Python, FastAPI, and AI project experience.",
  "skills": ["React", "Python", "FastAPI", "Supabase"],
  "target_roles": ["Software Engineer Intern", "Full Stack Intern"],
  "job_preferences": {
    "locations": ["San Francisco", "Remote"],
    "industries": ["AI", "Developer Tools", "B2B SaaS"]
  },
  "message_preferences": {
    "tone": "concise and confident",
    "length": "short",
    "personalization_level": "high"
  }
}
```

---

# Mocking Rules

## Mock External Providers

Do not use real external APIs in normal test runs.

Use mock clients for:

* Gemini
* Gmail
* Hunter
* scraper

Mock clients should return predictable data.

---

## Provider Mock Cases

Each provider should have reusable mock cases:

### Gemini

* successful dossier response
* successful message response
* timeout
* malformed response
* refusal/empty response

### Gmail

* successful send
* invalid recipient
* quota exceeded
* auth failure
* temporary failure

### Hunter

* email found
* no email found
* low confidence result
* rate limited
* provider error

### Scraper

* successful company list
* partial company scrape failure
* no companies found
* blocked website
* malformed page data

---

# Database Testing Rules

Tests that mutate the database must clean up after themselves.

Do not rely on data from previous tests.

Each test should create its own:

* user
* profile
* run
* company
* outreach rows

Tests should be isolated and repeatable.

---

# Status Transition Testing

Status transitions are core to ScoutReach.

Invalid transitions must be rejected.

Examples:

```text
draft -> approved is valid
approved -> sent is valid
sent -> draft is invalid
rejected company -> accepted may be allowed only if explicitly supported
failed send -> sent requires retry flow
```

If a transition rule changes, update tests and docs.

---

# Public Beta Safety Tests

Before public beta, these must pass:

* user cannot send without approving
* user cannot send another user's message
* auto-send is disabled or restricted
* rate limits block excessive sending
* failed Gmail send does not mark message as sent
* generated messages remain editable
* run failure is visible to user
* external API failures do not crash the app

---

# AI Agent Testing Instructions

When an AI agent changes code, it must:

1. Identify the touched feature area
2. Read the relevant testing section in this file
3. Add or update tests for changed behavior
4. Run the smallest relevant test command
5. Report which tests were run
6. Report any tests not run and why

Agents must not mark a task complete without mentioning test status.

---

# Test Command Documentation

Keep test commands updated in:

```text
/docs/COMMANDS.md
```

Examples:

```bash
pytest
npm run test
npm run lint
npm run typecheck
```

If commands change, update `/docs/COMMANDS.md`.

---

# What Not To Test Yet

Do not spend MVP time testing:

* exact design spacing
* animations
* minor copy changes
* every possible browser
* every edge case of every scraper page
* advanced analytics
* unpaid future features
* admin dashboards that do not exist yet

---

# Definition of Done

A feature is not done unless:

* implementation works
* relevant tests are added or updated
* relevant tests pass
* error states are handled
* ownership is validated
* docs are updated if behavior changed

For small docs-only changes, tests are not required.

---

# Final Rule

Testing should protect the product, not slow it to a crawl.

Write tests for the flows that would genuinely hurt users, corrupt data, waste API money, or damage sender reputation if broken.
