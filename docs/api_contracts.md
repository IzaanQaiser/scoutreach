# ScoutReach API Contracts

## Purpose

This document defines the backend API contract for ScoutReach.

The API is owned by the FastAPI backend. The frontend should only interact with the system through these endpoints. External services such as Playwright, Supabase, Gemini, Hunter.io, and Gmail should be called by the backend, not directly by the frontend.

---

# Global API Rules

## Base URL

Local development:

```text
http://localhost:8000
````

Production:

```text
https://api.scoutreach.com
```

---

## Authentication

All authenticated routes require the user to be logged in.

Recommended header:

```http
Authorization: Bearer <access_token>
```

The backend must resolve the authenticated user from this token and must not trust `user_id` from the frontend request body.

---

## Response Format

Successful responses should generally follow:

```json
{
  "success": true,
  "data": {}
}
```

Error responses should generally follow:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

---

## Common Error Codes

```text
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
VALIDATION_ERROR
RATE_LIMITED
RUN_ALREADY_ACTIVE
RUN_FAILED
SCRAPER_FAILED
GEMINI_FAILED
HUNTER_FAILED
GMAIL_FAILED
QUOTA_EXCEEDED
INTERNAL_SERVER_ERROR
```

---

## Common Status Values

### Run Status

```text
queued
running
scraping
enriching
dossier_generating
completed
completed_with_errors
failed
messages_generating
messages_generated
sending
```

### Company Status

```text
pending_review
accepted
rejected
dossier_failed
scrape_failed
email_lookup_failed
```

### Outreach Status

```text
draft
approved
needs_review
rejected
sending
sent
failed
generation_failed
```

---

# 1. Health Check

## `GET /health`

Checks whether the backend is alive.

### Response

```json
{
  "success": true,
  "data": {
    "status": "ok"
  }
}
```

---

# 2. Current User

## `GET /me`

Returns the authenticated user and profile setup status.

### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "premium_status": false,
      "tokens_used": 0,
      "auto_send_enabled": false,
      "first_name": "Izaan",
      "last_name": "Ali",
      "onboarding_status": "in_progress",
      "onboarding_step": "targets",
      "onboarding_completed_at": null,
      "message_preferences": {},
      "created_at": "2026-05-16T00:00:00Z",
      "updated_at": "2026-05-16T00:00:00Z"
    },
    "has_candidate_profile": true,
    "onboarding_complete": true
  }
}
```

---

## `PATCH /me`

Updates authenticated user identity fields used during onboarding.

### Request Body

```json
{
  "first_name": "Izaan",
  "last_name": "Ali"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Profile updated successfully",
    "onboarding_step": "profile_sources"
  }
}
```

---

# 3. Candidate Profile

## `GET /candidate-profile`

Fetches the authenticated user’s professional profile.

### Response

```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "resume": "Resume text...",
    "skills": {
      "languages": ["Python", "TypeScript"],
      "frameworks": ["Next.js", "FastAPI"]
    },
    "github_url": "https://github.com/example",
    "github_content": {},
    "linkedin_url": "https://linkedin.com/in/example",
    "linkedin_content": {},
    "portfolio_url": "https://example.com",
    "portfolio_content": {},
    "bio": "Short candidate bio.",
    "extra_context": "Extra personalization notes.",
    "target_roles": ["Software Engineer", "Full Stack Engineer"],
    "job_preferences": {
      "locations": ["San Francisco", "Remote"],
      "industries": ["AI", "Developer Tools"],
      "work_type": "internship"
    },
    "created_at": "2026-05-16T00:00:00Z",
    "updated_at": "2026-05-16T00:00:00Z"
  }
}
```

---

## `PUT /candidate-profile`

Creates or updates the authenticated user’s candidate profile.

### Request Body

```json
{
  "resume": "Resume text...",
  "skills": {
    "languages": ["Python", "TypeScript"],
    "frameworks": ["Next.js", "FastAPI"]
  },
  "github_url": "https://github.com/example",
  "linkedin_url": "https://linkedin.com/in/example",
  "portfolio_url": "https://example.com",
  "bio": "Short candidate bio.",
  "extra_context": "Extra personalization notes.",
  "target_roles": ["Software Engineer", "Full Stack Engineer"],
  "job_preferences": {
    "locations": ["San Francisco", "Remote"],
    "industries": ["AI", "Developer Tools"],
    "work_type": "internship"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Candidate profile saved successfully"
  }
}
```

---

# 4. User Settings

## `GET /settings`

Returns user-level settings.

### Response

```json
{
  "success": true,
  "data": {
    "auto_send_enabled": false,
    "message_preferences": {
      "tone": "casual",
      "length": "short",
      "personalization_level": "high"
    }
  }
}
```

---

## `PATCH /settings`

Updates user-level settings.

### Request Body

```json
{
  "auto_send_enabled": false,
  "message_preferences": {
    "tone": "casual",
    "length": "short",
    "personalization_level": "high",
    "cta_style": "direct"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Settings updated successfully"
  }
}
```

---

# 5. Onboarding

## `GET /onboarding/state`

Returns canonical onboarding routing state for the authenticated user.

### Response

```json
{
  "success": true,
  "data": {
    "status": "in_progress",
    "step": "calibration",
    "onboarding_complete": false,
    "calibration_loop_count": 1,
    "calibration_last_result": "partial_reject"
  }
}
```

---

## `POST /onboarding/example-messages`

Generates 5 calibration outreach examples for the current loop.

### Request Body

```json
{
  "loop_index": 0
}
```

### Response

```json
{
  "success": true,
  "data": {
    "loop_index": 0,
    "max_loops": 3,
    "examples": [
      {
        "example_id": "loop-1-example-1",
        "founder_name": "Founder 1",
        "company_name": "Example Technology Co 1-1",
        "target_role_context": "Software Engineer",
        "industry_context": "technology",
        "subject": "Short personalized subject",
        "message_content": "Draft message body..."
      }
    ]
  }
}
```

---

## `POST /onboarding/example-feedback`

Submits rejects/feedback for the current loop.

### Request Body

```json
{
  "loop_index": 0,
  "rejected_examples": [
    {
      "example_id": "loop-1-example-2",
      "position_industry_feedback": "More backend-focused companies",
      "subject_feedback": "Less generic subject line",
      "body_feedback": "Mention open source work directly"
    }
  ]
}
```

### Response (regenerated examples)

```json
{
  "success": true,
  "data": {
    "loop_index": 1,
    "max_loops": 3,
    "message": "Generated a refreshed example set based on your feedback.",
    "examples": []
  }
}
```

### Response (onboarding completed)

```json
{
  "success": true,
  "data": {
    "message": "Onboarding completed successfully",
    "status": "completed",
    "step": "done",
    "onboarding_complete": true
  }
}
```

---

## `POST /onboarding/complete`

Allows explicit onboarding completion (including calibration skip).

### Request Body

```json
{
  "completion_mode": "skipped_calibration"
}
```

`completion_mode` allowed values:

```text
completed
completed_after_cap
skipped_calibration
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Onboarding completed successfully",
    "status": "skipped_calibration",
    "step": "done",
    "onboarding_complete": true
  }
}
```

---

# 6. Runs

## `POST /runs`

Starts a new YC scraping run.

The backend must:

1. authenticate the user
2. check run quota
3. create a run row
4. snapshot the current candidate profile into `runs.profile_snapshot`
5. start the scraper job in the background
6. return `run_id` immediately

### Request Body

```json
{
  "selected_batches": ["W24", "S24", "W25"]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "status": "running",
    "progress": 0,
    "message": "Run started successfully"
  }
}
```

### Possible Errors

```text
UNAUTHORIZED
RATE_LIMITED
RUN_ALREADY_ACTIVE
VALIDATION_ERROR
INTERNAL_SERVER_ERROR
```

---

## `GET /runs`

Returns the authenticated user’s run history.

### Query Params

```text
limit?: number
offset?: number
status?: string
```

### Response

```json
{
  "success": true,
  "data": {
    "runs": [
      {
        "id": "uuid",
        "status": "completed",
        "progress": 100,
        "selected_batches": ["W25"],
        "started_at": "2026-05-16T00:00:00Z",
        "completed_at": "2026-05-16T00:10:00Z",
        "created_at": "2026-05-16T00:00:00Z"
      }
    ]
  }
}
```

---

## `GET /runs/{run_id}`

Returns details for a single run.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "selected_batches": ["W25"],
    "status": "completed",
    "progress": 100,
    "profile_snapshot": {},
    "error_message": null,
    "started_at": "2026-05-16T00:00:00Z",
    "completed_at": "2026-05-16T00:10:00Z",
    "created_at": "2026-05-16T00:00:00Z",
    "updated_at": "2026-05-16T00:10:00Z"
  }
}
```

---

## `GET /runs/{run_id}/status`

Used by the frontend polling loop.

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "status": "running",
    "progress": 64,
    "error_message": null,
    "companies_scraped": 32,
    "companies_total_estimate": 50,
    "messages_generated": 0,
    "messages_sent": 0
  }
}
```

---

# 7. Companies

## `GET /runs/{run_id}/companies`

Returns companies for a run.

### Query Params

```text
status?: pending_review | accepted | rejected | dossier_failed | scrape_failed | email_lookup_failed
limit?: number
offset?: number
```

### Example

```http
GET /runs/{run_id}/companies?status=pending_review
```

### Response

```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "id": "uuid",
        "run_id": "uuid",
        "name": "Example AI",
        "yc_url": "https://www.ycombinator.com/companies/example-ai",
        "website_url": "https://example.ai",
        "domain": "example.ai",
        "batch": "W25",
        "founders": [
          {
            "name": "Jane Founder",
            "linkedin_url": "https://linkedin.com/in/janefounder",
            "email": "jane@example.ai",
            "email_confidence": 89
          }
        ],
        "tags": ["AI", "Developer Tools"],
        "dossier": {
          "summary": "Example AI builds tools for developers.",
          "industry": "Developer Tools",
          "tech_stack_clues": ["Python", "LLMs"],
          "hiring_relevance": "Strong fit for full-stack AI candidates."
        },
        "status": "pending_review",
        "fit_score": 0.82,
        "created_at": "2026-05-16T00:00:00Z",
        "updated_at": "2026-05-16T00:00:00Z"
      }
    ]
  }
}
```

---

## `GET /companies/{company_id}`

Returns one company with full dossier.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "run_id": "uuid",
    "name": "Example AI",
    "yc_url": "https://www.ycombinator.com/companies/example-ai",
    "website_url": "https://example.ai",
    "domain": "example.ai",
    "batch": "W25",
    "founders": [],
    "raw_scraped_data": {},
    "website_content": {},
    "tags": [],
    "dossier": {},
    "status": "pending_review",
    "fit_score": 0.82,
    "created_at": "2026-05-16T00:00:00Z",
    "updated_at": "2026-05-16T00:00:00Z"
  }
}
```

---

## `PATCH /companies/{company_id}`

Updates the company review status after swiping.

### Request Body

```json
{
  "status": "accepted"
}
```

Allowed values:

```text
accepted
rejected
pending_review
```

### Response

```json
{
  "success": true,
  "data": {
    "company_id": "uuid",
    "status": "accepted",
    "message": "Company status updated successfully"
  }
}
```

---

## `GET /runs/{run_id}/companies/pending-count`

Returns how many companies still need review.

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "pending_count": 0
  }
}
```

---

# 8. Message Generation

## `POST /runs/{run_id}/generate-messages`

Generates outreach drafts for accepted companies.

The backend must:

1. check message generation quota
2. fetch accepted companies
3. fetch run profile snapshot and message preferences
4. generate one or more messages through Gemini
5. store each generated message in `outreach`
6. return a summary

### Request Body

```json
{
  "founder_selection_strategy": "first_verified_email",
  "max_messages": 25
}
```

Allowed `founder_selection_strategy` values:

```text
first_verified_email
all_verified_founders
manual_selected_founders
```

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "status": "messages_generated",
    "generated_count": 12,
    "generation_failed_count": 1,
    "message": "Messages generated successfully"
  }
}
```

### Possible Errors

```text
UNAUTHORIZED
NOT_FOUND
RATE_LIMITED
QUOTA_EXCEEDED
GEMINI_FAILED
VALIDATION_ERROR
INTERNAL_SERVER_ERROR
```

---

# 9. Outreach Review

## `GET /runs/{run_id}/outreach`

Returns outreach rows for a run.

### Query Params

```text
status?: draft | approved | needs_review | rejected | generation_failed | sending | sent | failed
limit?: number
offset?: number
```

### Response

```json
{
  "success": true,
  "data": {
    "outreach": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "run_id": "uuid",
        "company_id": "uuid",
        "company_name": "Example AI",
        "founder_name": "Jane Founder",
        "founder_email": "jane@example.ai",
        "subject": "Quick note on Example AI",
        "message_content": "Hey Jane, I came across Example AI...",
        "status": "draft",
        "review_notes": null,
        "error_message": null,
        "sent_at": null,
        "created_at": "2026-05-16T00:00:00Z",
        "updated_at": "2026-05-16T00:00:00Z"
      }
    ]
  }
}
```

---

## `GET /outreach/{outreach_id}`

Returns a single outreach record.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "run_id": "uuid",
    "company_id": "uuid",
    "founder_name": "Jane Founder",
    "founder_email": "jane@example.ai",
    "subject": "Quick note on Example AI",
    "message_content": "Hey Jane...",
    "status": "draft",
    "review_notes": null,
    "error_message": null,
    "sent_at": null,
    "created_at": "2026-05-16T00:00:00Z",
    "updated_at": "2026-05-16T00:00:00Z"
  }
}
```

---

## `PATCH /outreach/{outreach_id}`

Updates outreach status, subject, message body, or review notes.

### Request Body

```json
{
  "subject": "Updated subject",
  "message_content": "Updated message...",
  "status": "approved",
  "review_notes": "Looks good after edits."
}
```

Allowed statuses:

```text
draft
approved
needs_review
rejected
```

### Response

```json
{
  "success": true,
  "data": {
    "outreach_id": "uuid",
    "status": "approved",
    "message": "Outreach updated successfully"
  }
}
```

---

## `POST /outreach/{outreach_id}/regenerate`

Regenerates one outreach draft using user critique.

### Request Body

```json
{
  "critique": "Make it shorter and less formal.",
  "message_preferences_override": {
    "tone": "casual",
    "length": "short"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "outreach_id": "uuid",
    "subject": "New subject",
    "message_content": "Regenerated message...",
    "status": "draft",
    "message": "Message regenerated successfully"
  }
}
```

### Possible Errors

```text
UNAUTHORIZED
NOT_FOUND
RATE_LIMITED
GEMINI_FAILED
INTERNAL_SERVER_ERROR
```

---

## `GET /runs/{run_id}/outreach/review-summary`

Returns counts for the review UI.

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "counts": {
      "draft": 5,
      "approved": 12,
      "needs_review": 3,
      "rejected": 1,
      "sent": 0,
      "failed": 0,
      "generation_failed": 1
    }
  }
}
```

---

# 10. Sending

## Public MVP Rule

For the initial public MVP, the product should require manual review before sending.

Even if `auto_send_enabled` exists in the schema, the backend should not allow uncontrolled automatic sending for normal public users.

---

## `POST /runs/{run_id}/send-approved`

Sends all approved outreach messages for a run.

The backend must:

1. check sending quota
2. fetch approved outreach rows
3. send each email through Gmail
4. update each outreach row as `sent` or `failed`
5. return summary results

### Request Body

```json
{
  "send_mode": "approved_only"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "run_id": "uuid",
    "sent_count": 10,
    "failed_count": 1,
    "results": [
      {
        "outreach_id": "uuid",
        "status": "sent",
        "error_message": null
      },
      {
        "outreach_id": "uuid",
        "status": "failed",
        "error_message": "Gmail API failed"
      }
    ]
  }
}
```

### Possible Errors

```text
UNAUTHORIZED
NOT_FOUND
RATE_LIMITED
QUOTA_EXCEEDED
GMAIL_FAILED
INTERNAL_SERVER_ERROR
```

---

## `POST /outreach/{outreach_id}/send`

Sends a single approved outreach message.

### Request Body

```json
{
  "confirm_send": true
}
```

### Response

```json
{
  "success": true,
  "data": {
    "outreach_id": "uuid",
    "status": "sent",
    "sent_at": "2026-05-16T00:00:00Z"
  }
}
```

---

# 11. Logs

## `GET /runs/{run_id}/logs`

Returns logs for a run.

Recommended for debugging scraper, Gemini, Hunter, and Gmail failures.

### Response

```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": "uuid",
        "run_id": "uuid",
        "level": "info",
        "message": "Started scraper job",
        "metadata": {},
        "created_at": "2026-05-16T00:00:00Z"
      }
    ]
  }
}
```

---

# 12. Quotas / Rate Limits

## Recommended MVP Limits

These are implementation defaults, not strict final product rules.

```text
runs_per_day: 3
companies_per_run: 50
message_generations_per_day: 100
regenerations_per_day: 50
emails_sent_per_day: 25
```

---

## `GET /quotas`

Returns quota usage for the authenticated user.

### Response

```json
{
  "success": true,
  "data": {
    "runs": {
      "used": 1,
      "limit": 3
    },
    "message_generations": {
      "used": 12,
      "limit": 100
    },
    "regenerations": {
      "used": 4,
      "limit": 50
    },
    "emails_sent": {
      "used": 10,
      "limit": 25
    }
  }
}
```

---

# 13. Frontend Polling Contract

The frontend should poll:

```http
GET /runs/{run_id}/status
```

Recommended interval:

```text
3 seconds
```

Polling should stop when run status is:

```text
completed
completed_with_errors
failed
messages_generated
```

---

# 14. Security Rules

The backend must enforce:

```text
- A user can only access their own runs.
- A user can only access companies belonging to their own runs.
- A user can only access outreach rows belonging to their own user_id.
- The frontend must never be trusted to provide user_id.
- Sending emails must require authenticated user ownership.
- Public MVP must require manual review before sending.
```

---

# 15. MVP Endpoint Checklist

Required for first working MVP:

```text
GET /health
GET /me
PATCH /me
GET /candidate-profile
PUT /candidate-profile
GET /settings
PATCH /settings
GET /onboarding/state
POST /onboarding/example-messages
POST /onboarding/example-feedback
POST /onboarding/complete
POST /runs
GET /runs
GET /runs/{run_id}
GET /runs/{run_id}/status
GET /runs/{run_id}/companies
GET /companies/{company_id}
PATCH /companies/{company_id}
GET /runs/{run_id}/companies/pending-count
POST /runs/{run_id}/generate-messages
GET /runs/{run_id}/outreach
GET /outreach/{outreach_id}
PATCH /outreach/{outreach_id}
POST /outreach/{outreach_id}/regenerate
GET /runs/{run_id}/outreach/review-summary
POST /runs/{run_id}/send-approved
POST /outreach/{outreach_id}/send
GET /runs/{run_id}/logs
GET /quotas
