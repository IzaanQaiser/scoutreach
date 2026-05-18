# MVP_SCOPE.md

# Purpose

This document defines the exact scope of the ScoutReach MVP/public beta.

Its purpose is to:
- prevent scope creep
- maintain engineering velocity
- keep the product lean
- guide AI coding agents
- clarify what is intentionally NOT being built yet

Anything outside this document should be treated as out of scope unless explicitly approved.

---

# MVP Objective

ScoutReach MVP exists to validate one core workflow:

```text
Users can discover YC startups, evaluate startup matches, generate personalized founder outreach, review/edit the outreach, and send messages efficiently.
````

The MVP is NOT attempting to:

* automate the entire recruiting process
* become a CRM
* become a sales platform
* become a recruiter marketplace
* become a networking social platform

The MVP only needs to prove:

* users find value in startup discovery + AI-assisted outreach
* users are willing to use generated outreach workflows
* users can efficiently identify high-fit startups
* personalized outreach improves response rates or workflow quality

---

# MVP User Flow

The MVP user flow is:

```text
Onboarding
→ Start Run
→ Scrape YC Companies
→ Generate Company Dossiers
→ Tinder-Style Match Evaluation
→ Generate Outreach Drafts
→ Review / Edit Outreach
→ Send Approved Outreach
→ View Results
```

This flow is the core product.

Anything outside this flow should be treated as secondary.

---

# MVP Features

## Included Features

### Authentication

* user signup/login
* secure sessions
* user-specific data isolation

---

### Candidate Profile

Users can:

* upload resume
* add GitHub URL
* add LinkedIn URL
* define target roles
* define job preferences
* define message preferences

---

### YC Batch Selection

Users can:

* select YC batches to scrape
* start runs

---

### Run System

The system supports:

* run creation
* run progress tracking
* run completion/failure states
* run history

---

### Scraping Pipeline

The scraper supports:

* YC company scraping
* founder extraction
* founder LinkedIn extraction
* company website scraping
* website content extraction

---

### AI Dossier Generation

Gemini generates:

* company summaries
* industry classification
* startup understanding
* inferred hiring relevance
* tags/metadata
* fit information

---

### Founder Email Enrichment

Hunter integration supports:

* founder email lookup
* email confidence metadata

---

### Match Evaluation

Users can:

* swipe right to accept companies
* swipe left to reject companies
* review company dossiers before generating outreach

---

### Outreach Generation

Gemini generates:

* personalized outreach subjects
* personalized outreach message bodies

using:

* user profile
* job preferences
* company dossier
* founder information
* scraped context

---

### Outreach Review

Users can:

* approve drafts
* edit drafts
* regenerate drafts
* reject drafts
* mark drafts for further review

---

### Sending

Users can:

* send approved outreach through Gmail integration

The MVP should default to:

* manual review before sending

Auto-send should NOT be public default behavior.

---

### Dashboard

Users can:

* view runs
* view outreach history
* view sent/failed statuses
* track generated outreach

---

### Rate Limiting

The MVP includes:

* run creation limits
* generation limits
* sending limits
* regeneration limits

---

### Error Handling

The MVP includes:

* failed run handling
* failed generation handling
* failed send handling
* surfaced error states
* stored error messages

---

# Explicitly Out of Scope

The following are intentionally NOT part of the MVP.

AI agents and contributors should NOT implement these systems unless explicitly instructed.

---

## Browser Extension

NOT included:

* Chrome extension
* browser automation assistant
* page overlays

---

## LinkedIn Automation

NOT included:

* LinkedIn messaging automation
* LinkedIn login automation
* browser-based outreach bots
* session hijacking
* automated LinkedIn actions

---

## Reply Tracking

NOT included:

* inbox parsing
* response classification
* automated reply detection
* sentiment analysis
* conversation threading

---

## CRM Functionality

NOT included:

* pipeline management
* contact stages
* Kanban systems
* sales workflows
* lead assignment

---

## Multi-User Collaboration

NOT included:

* teams
* shared workspaces
* permissions systems
* organization accounts

---

## Analytics Platform

NOT included:

* advanced dashboards
* conversion funnels
* detailed analytics
* cohort analysis
* campaign reporting

Simple stats/history are acceptable.

---

## Autonomous AI Outreach

NOT included:

* fully autonomous messaging
* unsupervised sending
* autonomous decision-making loops
* AI-controlled outreach campaigns

Human review remains central to MVP behavior.

---

## Email Warmup Infrastructure

NOT included:

* deliverability systems
* inbox warmup
* spam optimization systems
* email reputation systems

---

## Background Queue Infrastructure

NOT included initially:

* Kafka
* Redis queues
* Celery clusters
* distributed workers

Simple async/background execution is acceptable.

---

## Mobile Applications

NOT included:

* iOS app
* Android app
* React Native app

---

## Complex Personalization Memory

NOT included:

* long-term learning systems
* vector memory systems
* behavioral personalization engines
* reinforcement learning loops

Simple stored preferences are sufficient.

---

## Full Recruiting Platform

NOT included:

* job boards
* ATS integrations
* applicant tracking
* recruiter-facing systems
* candidate ranking marketplaces

---

# MVP Success Criteria

The MVP is successful if users can:

* onboard successfully
* complete runs successfully
* review startups efficiently
* generate useful outreach drafts
* edit drafts comfortably
* send outreach reliably

without:

* major confusion
* major instability
* major workflow friction

---

# Engineering Priorities

The MVP prioritizes:

1. Correctness
2. Stability
3. Simplicity
4. Speed of iteration
5. Clear UX
6. Debuggability

The MVP does NOT prioritize:

* extreme scalability
* perfect optimization
* enterprise architecture
* maximum abstraction

---

# Product Priorities

The MVP should feel:

* fast
* clean
* understandable
* controlled
* trustworthy

The product should NOT feel:

* spammy
* chaotic
* over-automated
* overwhelming

---

# AI Agent Rules

AI coding agents working on ScoutReach MUST:

* stay within MVP scope
* avoid speculative features
* avoid infrastructure overengineering
* avoid dependency bloat
* avoid architecture redesigns
* preserve manual review workflows
* preserve editability of generated outreach

If functionality is unclear:

* implement the simplest safe version
* leave TODOs when appropriate
* avoid inventing extra systems

---

# Final Principle

ScoutReach MVP exists to validate a focused workflow.

Every engineering and product decision should support:

```text
discover → evaluate → generate → review → send
```

Anything outside that loop should be considered non-essential during MVP development.
