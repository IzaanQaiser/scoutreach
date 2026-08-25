# ScoutReach — Project Brief

## Overview

ScoutReach is an AI-powered founder outreach platform designed to help users discover high-fit startup opportunities and generate personalized outreach at scale.

The system scrapes and enriches Y Combinator startup data, builds AI-generated company dossiers, allows users to evaluate companies through a Tinder-style matching interface, and generates personalized founder outreach drafts using the user’s professional background and preferences.

The MVP focuses on:

* YC startup discovery
* company enrichment
* swipe-based evaluation
* AI-generated personalized outreach
* manual review before sending
* Gmail-based sending workflow

The goal of the MVP is to create a fast, highly usable outreach workflow that dramatically reduces the time required to identify and contact relevant startups while maintaining high personalization quality.

---

# Core Product Flow

1. User creates account and onboarding profile
2. User uploads/provides:

   * resume
   * GitHub
   * LinkedIn
   * portfolio
   * job preferences
3. User selects YC batches and starts a run
4. System scrapes YC companies and company websites
5. AI generates structured company dossiers
6. Hunter enriches founder emails
7. User evaluates companies in Tinder-style swipe flow
8. User generates outreach drafts
9. User reviews/edits/regenerates drafts
10. User manually sends approved outreach
11. Dashboard tracks outreach history and results

---

# MVP Goals

The MVP should prioritize:

* speed
* clarity
* reliability
* strong UX
* minimal friction
* lean architecture

The MVP is NOT trying to:

* automate all recruiting
* mass spam founders
* become a CRM
* become LinkedIn
* become a fully autonomous AI agent

The product should feel:

* fast
* modern
* simple
* high-signal
* founder-focused

---

# MVP Scope

## Included

### Authentication

* Google login
* persistent user sessions

### Candidate Profile

* resume upload/input
* GitHub URL
* LinkedIn URL
* portfolio URL
* bio
* target roles
* job preferences
* message preferences

### Run System

* create run
* select YC batches
* track progress
* status polling

### Scraping

* YC company scraping
* founder extraction
* company website scraping
* company metadata extraction

### AI Enrichment

* company dossier generation
* startup categorization
* relevance metadata
* outreach generation

### Founder Email Enrichment

* Hunter.io integration
* founder email lookup

### Match Evaluation

* Tinder-style swipe interface
* accept/reject companies

### Outreach Generation

* personalized subject lines
* personalized founder messages
* regenerate functionality

### Message Review

* approve
* reject
* edit
* regenerate

### Sending

* Gmail integration
* manual review before send
* send approved messages

### Dashboard

* run history
* outreach history
* sent/failed status tracking

---

# Explicitly Out of Scope (Initial MVP)

The MVP should NOT include:

* autonomous outbound sending
* LinkedIn automation
* browser automation for applications
* analytics dashboards
* open/reply tracking
* CRM pipelines
* team collaboration
* mobile apps
* browser extension
* multi-provider email sending
* complex recommendation systems
* real-time websocket architecture
* queue orchestration systems
* advanced ranking algorithms
* fine-tuned AI models
* distributed scraping systems

If something is not necessary for:

1. generating high-quality outreach
2. reviewing messages
3. sending outreach

then it should likely not exist in the MVP.

---

# Core UX Principles

## 1. Minimal Friction

The user should move through the product quickly without unnecessary forms or setup complexity.

## 2. Fast Feedback

Runs, scraping, and message generation should provide visible progress and feedback.

## 3. Human Oversight

The public MVP should require manual review before sending messages.

## 4. High Signal

The system should prioritize fewer, higher-quality startup matches over massive quantity.

## 5. Simplicity Over Cleverness

The architecture and UI should remain understandable and maintainable.

---

# Public MVP Rules

## Manual Review Required

Auto-send should NOT be enabled by default for public users.

Users must:

* review drafts
* approve drafts
* explicitly trigger sending

## Rate Limits Required

The backend must enforce:

* run limits
* message generation limits
* regeneration limits
* sending limits

## Error Visibility

Failures should be surfaced clearly:

* scraping failures
* Gemini failures
* Hunter failures
* Gmail failures

---

# High-Level Architecture

## Frontend

* Next.js
* dashboard UI
* swipe UI
* review UI
* onboarding UI

## Backend

* FastAPI
* orchestration layer
* API layer
* generation coordination
* sending coordination

## Database

* Supabase PostgreSQL
* stores:

  * users
  * runs
  * companies
  * outreach
  * profile snapshots

## Scraper

* Playwright
* YC scraping
* company website scraping

## AI Layer

* Gemini API
* dossier generation
* outreach generation

## Email Enrichment

* Hunter.io API

## Sending

* Gmail API

---

# Database Philosophy

The database is structured around the concept of a “run.”

A run represents one full:

* scrape
* enrich
* evaluate
* generate
* outreach cycle

Core relationships:

* user → many runs
* run → many companies
* run → many outreach drafts
* company → many outreach drafts

The architecture should support:

* retries
* regeneration
* history
* debugging
* future analytics

without requiring major rewrites.

---

# Development Philosophy

## Keep the Repo Lean

Avoid:

* premature abstractions
* excessive dependencies
* over-engineering
* unnecessary services

## Prefer Explicit Code

Readable and boring code is preferred over clever patterns.

## Build Incrementally

Implement:

1. core functionality
2. stability
3. UX polish
4. optimization

in that order.

## One Responsibility Per Component

* scraper scrapes
* Gemini generates
* backend orchestrates
* DB stores state

---

# Initial Build Order

## Phase 1

* repo setup
* FastAPI
* Supabase
* auth
* DB schema

## Phase 2

* run creation
* scraper integration
* company persistence

## Phase 3

* Gemini dossier generation
* Hunter enrichment

## Phase 4

* swipe UI
* company evaluation

## Phase 5

* outreach generation
* draft persistence

## Phase 6

* review/edit/regenerate
* Gmail sending

## Phase 7

* polish
* rate limits
* error handling
* public beta readiness

---

# Success Criteria for MVP

The MVP is successful if a user can:

1. create a profile
2. run a YC scrape
3. evaluate startups
4. generate personalized outreach
5. review/edit messages
6. send approved outreach
7. track results

without major confusion or instability.

---

# Long-Term Direction (Not MVP)

Potential future directions:

* better startup ranking
* behavioral personalization
* AI-assisted follow-ups
* email analytics
* recruiter/startup matching
* recommendation systems
* CRM integrations
* collaborative outreach
* outbound optimization
* autonomous workflows

These should NOT influence MVP complexity unless required immediately.
