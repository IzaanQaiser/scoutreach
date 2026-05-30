# AUTH_ONBOARDING_BUILD_BLUEPRINT.md

# ScoutReach Auth + Onboarding Build Blueprint

This is the single-link implementation blueprint for login, signup, onboarding, and message-style calibration.

Use this document as the primary source when building the missing pre-dashboard user flow.

This doc formalizes:
- exact user flow from funnel entry to dashboard access
- required backend/frontend states
- required API and schema changes
- route guard rules
- calibration loop behavior
- phased implementation order and acceptance gates
- test plan and release checklist

---

# 1. Scope and Intent

## Goal

Implement a complete public-MVP auth + onboarding flow that:
- supports signup/login
- collects user identity + profile context
- collects target role/industry/preferences
- calibrates message style through sample swipe feedback
- gates dashboard until onboarding is complete

## Non-Goals (for this build)

Do NOT add:
- enterprise SSO
- team/org auth
- advanced analytics dashboards
- autonomous sending
- CRM features

Keep this implementation lean and MVP-safe.

---

# 2. Source Alignment (Must Stay Consistent)

This blueprint is aligned with:
- `/docs/brief.md`
- `/docs/mvp_scope.md`
- `/docs/architecture.md`
- `/docs/api_contracts.md`
- `/docs/db_schema.md`
- `/docs/system_invariants.md`

If this doc conflicts with invariant docs:
- follow `/docs/system_invariants.md` first
- then update this doc in the same change

---

# 3. Canonical UX Flow (Formalized)

## 3.1 Entry

User enters via:
- QR code
- direct URL
- outreach funnel link/ad

All entries land on `Landing/Login`.

## 3.2 Landing/Auth

1. Landing page is shown.
2. User clicks `Get Started`.
3. Landing transitions into `Login/Signup` state.
4. User chooses:
- `Log in` (returning user)
- `Sign up` (new user)

## 3.3 Returning User Branch

After successful login:
1. fetch `/me`
2. evaluate onboarding status
3. route:
- if complete -> `/dashboard`
- if incomplete -> resume at saved onboarding step

## 3.4 New User Branch

After successful signup:
- create user session
- create/update baseline user row
- route to onboarding Step 1

## 3.5 Onboarding Steps (Linear, Back/Next)

### Step 1: Name Collect
Collect:
- first name
- last name (or display name fallback)

Primary action:
- `Next`

Secondary action:
- `Back`

### Step 2: Resume/GitHub/Portfolio Collect
Collect:
- resume text or upload
- GitHub URL
- portfolio URL
- LinkedIn URL (optional in UI but allowed by backend)

Primary action:
- `Next`

Secondary action:
- `Back`

### Step 3: Industry + Target Roles Collect
Collect:
- target roles
- preferred industries
- job preference context (location/work type if provided)

Primary action:
- `Next`

Secondary action:
- `Back`

### Step 4: Message Style/Tone Preferences
Collect:
- tone
- style
- length
- personalization level

Primary action:
- `Next`

Secondary action:
- `Back`

### Step 5: Message Calibration
Show loading state:
- `Generating some example messages...`

Optional control:
- `Skip this step`

Then show 5 swipeable examples:
- fake founder name
- fake company
- real user target role/industry context
- synthetic subject line
- synthetic message body

Swipe result branches:
- all accepted -> completion message -> animation -> dashboard
- some rejected -> collect structured feedback -> regenerate -> loop

### Step 6: Rejection Feedback + Regeneration
If any examples rejected:
- show “help us understand what you don’t like” form
- capture feedback by area:
  - position/industry fit
  - subject/header
  - body style/content

Regenerate examples from feedback and return to swipe set.

### Step 7: Calibration Loop Control
- max loop count: 3 total cycles
- if user still rejects messages after max loops:
  - mark calibration as capped
  - continue to dashboard
  - show message that preferences can be tuned later in Settings

---

# 4. Required State Model

## 4.1 User-Level State

Track on server:
- `onboarding_status`: `not_started | in_progress | completed | completed_after_cap | skipped_calibration`
- `onboarding_step`: `auth | name | profile_sources | targets | message_preferences | calibration | done`
- `onboarding_completed_at`: timestamp nullable

## 4.2 Calibration State

Track on server:
- `calibration_loop_count`: integer (0..3)
- `calibration_last_result`: `accepted_all | partial_reject | loop_cap_exit | skipped`

## 4.3 Route Guard State

Derived from `/me`:
- authenticated?
- onboarding complete?
- if incomplete, which step?

---

# 5. Required Route Map (Frontend)

Minimum route set:
- `/` -> marketing/landing + Get Started
- `/auth` -> login/signup view
- `/onboarding/name`
- `/onboarding/profile-sources`
- `/onboarding/targets`
- `/onboarding/message-preferences`
- `/onboarding/calibration`
- `/onboarding/done` (short completion transition)
- `/dashboard`

Guard rules:
- unauthenticated user cannot access onboarding/dashboard
- authenticated + incomplete onboarding cannot access dashboard
- authenticated + complete onboarding should be redirected away from onboarding routes to dashboard

---

# 6. Backend Contract Plan

Use existing endpoints where possible and add only what is needed.

## 6.1 Existing Endpoints to Reuse

- `GET /me`
- `PUT /candidate-profile`
- `GET /candidate-profile`
- `PATCH /settings`
- `GET /settings`

## 6.2 Required Endpoint Additions

### `PATCH /me`
Purpose:
- update identity basics needed by Step 1 (name fields)

Request:
- `first_name`
- `last_name`

Response:
- updated user summary + onboarding step

### `GET /onboarding/state`
Purpose:
- return canonical onboarding routing state

Response:
- onboarding status
- step
- calibration loop count

### `POST /onboarding/example-messages`
Purpose:
- generate 5 calibration examples

Behavior:
- enforce per-user calibration generation quota
- use provider-safe retry/backoff
- persist calibration session/event metadata

### `POST /onboarding/example-feedback`
Purpose:
- submit rejection feedback and regenerate examples

Behavior:
- increment loop count
- enforce max loop constraint
- return next example set or cap-complete response

### `POST /onboarding/complete`
Purpose:
- mark onboarding complete and set completion timestamps/status

Note:
- can be called by accepted-all path, skip path, or cap-exit path

---

# 7. Database Plan

## 7.1 `users` Table Additions

Add columns:
- `first_name text`
- `last_name text`
- `onboarding_status text not null default 'not_started'`
- `onboarding_step text not null default 'auth'`
- `onboarding_completed_at timestamptz null`

Add constraints:
- check allowed onboarding status values
- check allowed onboarding step values

## 7.2 New Table: `onboarding_calibration_events`

Purpose:
- durable tracking of calibration generation/regeneration attempts
- quota and loop enforcement

Recommended columns:
- `id uuid pk`
- `user_id uuid fk users`
- `event_type text` (`examples_generated | feedback_submitted | skipped | completed`)
- `loop_index integer`
- `feedback jsonb default '{}'`
- `created_at timestamptz default now()`

Indexes:
- `(user_id, created_at)`
- `(user_id, event_type)`

---

# 8. Calibration Behavior Contract

## Example Set Requirements

Each set always contains exactly 5 examples.

Each example contains:
- `example_id`
- `founder_name` (synthetic)
- `company_name` (synthetic)
- `target_role_context` (real from user preferences)
- `industry_context` (real from user preferences)
- `subject`
- `message_content`

## Feedback Schema (from rejected examples)

For each rejected example, allow structured feedback fields:
- `position_industry_feedback`
- `subject_feedback`
- `body_feedback`

## Loop Rules

- max loops = 3
- skip is allowed and should complete onboarding with explicit status
- all accepted should immediately complete onboarding

---

# 9. Safety, Quotas, and Provider Rules

Must enforce server-side:
- auth ownership checks
- onboarding endpoints scoped to current authenticated user
- per-user onboarding/calibration quotas
- provider retry with exponential backoff + jitter on transient failures
- bounded provider throttling between calls

Do NOT:
- run unbounded synchronous fan-out
- trust client onboarding completion flags

---

# 10. Implementation Order (Step-by-Step)

## Phase A: Auth + Guard Foundation

1. implement frontend auth shell routes (`/`, `/auth`)
2. implement Supabase session handling in frontend
3. implement route guard middleware/utilities
4. add backend `PATCH /me` for name capture
5. extend `/me` payload with onboarding routing fields

Exit criteria:
- login/signup works
- auth redirects work
- dashboard blocked for incomplete onboarding

## Phase B: Onboarding Data Capture

1. implement onboarding routes for steps 1-4
2. persist step1 via `PATCH /me`
3. persist step2/3 via `PUT /candidate-profile`
4. persist step4 via `PATCH /settings`
5. persist `onboarding_step` progression server-side

Exit criteria:
- refreshing any step does not lose saved data
- user can resume onboarding from saved step

## Phase C: Calibration Engine

1. add onboarding calibration event table + migration
2. add example generation + feedback endpoints
3. implement 5-example swipe UI
4. implement rejection feedback UI
5. implement loop max=3 enforcement and skip path

Exit criteria:
- accepted-all, partial-reject-loop, skip, and cap-exit all work

## Phase D: Completion + Settings Hand-off

1. implement onboarding complete endpoint
2. route to `/onboarding/done` then `/dashboard`
3. ensure Settings can edit captured preferences post-onboarding
4. finalize guard behavior for complete users

Exit criteria:
- onboarding completion is durable
- complete users always reach dashboard

---

# 11. Test Plan (Required)

## Backend Integration

- signup/login authenticated user can call onboarding APIs
- `PATCH /me` updates names + onboarding step
- onboarding state endpoint returns correct routing decision
- calibration generation enforces quota
- feedback loop increments and caps at 3
- onboarding complete status cannot be spoofed client-side

## Frontend Integration/E2E

- new user full happy path reaches dashboard
- returning incomplete user resumes correct step
- skip calibration path reaches dashboard
- all-accepted path reaches dashboard
- repeated rejection path caps and reaches dashboard
- route guards prevent unauthorized dashboard access

## Regression

- existing run/review/generate/send flow remains unaffected
- ownership invariants still hold

---

# 12. Acceptance Checklist

A phase is complete only when all are true:
- required routes exist and are guarded correctly
- onboarding steps persist and resume reliably
- calibration loop behavior matches contract
- dashboard access is blocked until completion
- tests pass for happy + edge + security paths
- docs (`api_contracts`, `db_schema`, `architecture`, `known_gaps`, `decisions`) updated with implemented behavior

---

# 13. Post-Implementation Doc Update Requirements

When implementation is complete, update:
- `/docs/api_contracts.md` with final onboarding/auth endpoints and payloads
- `/docs/db_schema.md` with final onboarding fields/tables
- `/docs/architecture.md` onboarding sequence to match implementation
- `/docs/decisions.md` key auth/onboarding tradeoffs
- `/docs/known_gaps.md` remaining onboarding limitations

---

# 14. Open Decisions To Lock Before Coding

These decisions should be confirmed before implementation starts:

1. Auth providers in MVP:
- Google only
- or Google + email/password

2. Resume input mode in Step 2:
- text paste only
- file upload + extraction
- both

3. Calibration skip behavior:
- always allowed
- allowed only after first example set

4. Dashboard unlock rule after loop cap:
- unlock immediately after 3 loops
- require minimum accepted count before unlock

5. Required fields for onboarding completion:
- strict minimum set
- soft completion with warnings

---

# 15. Final Rule

Keep this implementation explicit and boring.

Do not redesign the product architecture during onboarding build.
Use the minimum system that cleanly satisfies the flow above.
