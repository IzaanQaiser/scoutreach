# Task Title

Short descriptive name for the task.

Example:
- Implement run creation endpoint
- Add outreach regeneration flow
- Build swipe review UI

---

# Goal

Describe exactly what should be built.

Be specific.

Include:
- desired behavior
- user outcome
- backend/frontend expectations

Example:
Create the backend endpoint and service logic required to start a new run, create the database row, trigger the scraper pipeline, and return the run ID to the frontend.

---

# Why

Explain why this task exists.

Examples:
- enables scrape pipeline
- required for onboarding flow
- supports public beta review workflow

This helps the agent make better implementation decisions.

---

# Relevant Documentation

List all relevant documents the agent must read before implementing.

Example:

- docs/PROJECT_BRIEF.md
- docs/ARCHITECTURE.md
- docs/API_CONTRACTS.md
- docs/DB_SCHEMA.md
- docs/DEVELOPMENT_STANDARDS.md
- docs/STATUS_ENUMS.md

---

# Relevant Files

List files or directories relevant to the task.

Example:

Backend:
- backend/app/api/runs.py
- backend/app/services/run_service.py
- backend/app/db/run_repository.py

Frontend:
- frontend/app/dashboard/page.tsx

---

# Scope

Define exactly what IS included.

Example:
- create route
- create service
- create DB insert
- create polling endpoint
- update run status

---

# Out of Scope

Define exactly what is NOT included.

Example:
- scraper implementation
- frontend styling polish
- retry queues
- analytics
- email sending

This is critical for preventing scope creep.

---

# Functional Requirements

List exact behaviors the implementation must support.

Example:

1. User can create a run using selected YC batches
2. Run row is inserted into database
3. Run status defaults to "running"
4. Endpoint returns run_id
5. User ownership validation is required
6. Invalid requests return structured errors

---

# Technical Constraints

List architectural rules that must be followed.

Example:

- No business logic inside route handlers
- Use service layer
- Use repository layer for DB access
- No new dependencies
- Preserve current architecture
- Use existing status enums
- Keep implementation explicit and simple

---

# API Requirements

If relevant, define:
- endpoint
- request body
- response body
- status codes

Example:

Endpoint:
POST /runs

Request:
{
  "selected_batches": ["W24", "S24"]
}

Response:
{
  "run_id": "...",
  "status": "running"
}

---

# Database Requirements

Describe required DB changes.

Example:
- insert into RUNS table
- update progress field
- preserve profile_snapshot

If no DB changes are needed:
```text
No schema changes required.
````

---

# Frontend Requirements

Describe UI behavior if frontend is involved.

Example:

* show loading spinner
* poll every 3 seconds
* show error state
* disable duplicate submissions

---

# Error Handling Requirements

List required failure behavior.

Example:

* invalid auth returns 401
* invalid ownership returns 403
* scraper startup failure updates run status to failed
* structured error responses required

---

# Logging Requirements

List important events that must be logged.

Example:

* run_created
* run_failed
* scraper_started
* scraper_failed

---

# Testing Requirements

List required tests.

Example:

Backend:

* successful run creation
* invalid auth rejection
* invalid payload rejection

Frontend:

* loading state
* error state
* success redirect

---

# Acceptance Criteria

The task is complete ONLY when:

* endpoint works
* tests pass
* types pass
* lint passes
* loading/error states exist
* docs updated if architecture changed

---

# Deliverables

List exactly what should exist after completion.

Example:

* new API endpoint
* service implementation
* repository methods
* tests
* updated docs

---

# Notes

Optional implementation notes or warnings.

Example:
Do not implement retry queues yet.
Keep scraper triggering synchronous for MVP.

