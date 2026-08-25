# ScoutReach v2 — Phase Plan

Engineering roadmap from the current scaffold (Phase 0, done) to a
pilot-ready product. Each phase maps to pipeline stages in
`scoutreach-new.md` §9/§9.1 and rolls up into the spec's own v0.1/v0.2/v0.3
calendar (§12). A phase is not done until its tests are green and its pass
criteria are met — no phase ships on "looks right."

Test types used below: **unit** (pure logic, fixtures, no I/O), **integration**
(DB + mocked providers), **manual** (a real run against a live provider,
done once per phase, not repeated in CI).

---

## Phase 0 — Repo scaffold — done

Drizzle schema for `companies`/`company_evidence`/`contacts`/`events`, DB
client, stubbed pipeline modules, `ContactProvider` interface. See commits
on `main`. No tests yet — nothing functional exists.

---

## Phase 1 — Company sourcing (stage [1]) · v0.1

**Builds:** topstartups.io scraper, raw-response disk cache, `companies`
persistence.

Investigated directly (2026-08-25): topstartups.io is Django-rendered
HTML, not Airtable/JSON as originally guessed. Its `robots.txt` disallows
`/*?page=` — the mechanism its listing uses past 20 results — so the
scraper slices spec §2's target filters (size × funding round × location
× industry, via `company_size`/`funding_round`/`hq_location`/`industries`
GET params, all combinable) finely enough to stay under the page-1 cap
instead of paginating. Implemented in `lib/pipeline/scrape.ts`.

Of the quality bar's 4 criteria (§2), only 2 are mechanically checkable at
scrape time: headcount (guaranteed by the slice's own filter) and funding
recency (`passesFundingRecency`, ≤2 years). "Nameable product/buyer" is a
human judgment call and "public engineering surface" is Phase 2's job
(evidence crawl) — Phase 1 persists every scraped row as `status="new"`
rather than pretending to gate on criteria it can't check yet.

**Tests**
- unit: card parser against a saved real-HTML fixture → expected
  `ScrapedCompany[]` fields (name/domain/url/stage/location/investors),
  including the amount-prefix-in-funding-round edge case ("$30M Seed")
- unit: `passesFundingRecency` boundary cases
- unit: `buildFilterSlices` metro→city expansion and cartesian product
- integration: second scrape run against the same inputs makes zero network
  calls (cache hit) — `http-cache.test.ts`

**Pass criteria:** ≥100 real companies persisted, 0 duplicate domains,
`raw_json` populated on 100% of rows, cache verified via test. All of the
above are implemented and green (13/13 tests) as of this phase.

---

## Phase 2 — Evidence crawl (stage [2]) · v0.1

**Builds:** per-company crawl of `/blog`, `/changelog`, `/docs`,
`/careers`, `/engineering` off the company's own domain, plus its GitHub
org when known. Stores url + title + exact snippet + `retrieved_at`.
Implemented in `lib/pipeline/evidence.ts`, sharing the rate-limited disk
cache from Phase 1 (`http-cache.ts`).

"Recent news" (the 6th source in §9.1) is deliberately not implemented —
it needs a search provider (news API or Google News RSS), a separate
decision, not a direct fetch like the rest of this stage. Left as a TODO
in the module; doesn't block the rest of the phase.

Verified directly against a real site (2026-08-25, avoca.ai): modern
startup sites are often Next.js/React SPAs, but content is still
server-rendered into the initial HTML — plain fetch + strip noise tags +
read visible text works without a headless browser. 3 of 5 direct paths
resolved on that real site, confirming per-path failures are the normal
case, not an edge case.

**Tests**
- unit: snippet extraction on a real trimmed fixture (verbatim substring,
  not paraphrased) plus synthetic noise-stripping and empty-page cases
- unit: `crawlEvidence` skips 404s without throwing; includes a GitHub
  org row when provided
- integration: a company whose fetch throws (DNS/connection failure)
  doesn't stop the batch — `crawlEvidenceForCompanies` still processes
  the rest and flags the failed one via `evidenceStatusFor`

**Pass criteria:** 100% of rows have a resolvable URL and non-empty
snippet (enforced structurally — empty extractions are never persisted);
zero-evidence companies get `status="needs_evidence"`, never dropped.
All implemented and green (8/8 new tests). The "≥3 rows for ≥80% of
companies" volume target can only be measured once Phase 1 runs against
real scraped companies, not fixtures.

---

## Phase 3 — Contacts, ranking, v0.1 export · v0.1 milestone

**Builds:** Apollo People Search (`ContactProvider.search`, 0-credit), rank
scoring (`rank.ts`, formula in file comment — implement as written), CSV
export, `/app/companies` sortable table.

**Tests**
- unit: rank formula against a fixed input→score table covering every
  `title_weight` tier and every modifier
- unit: selection rule (≥1 budget-owner, ≤1 recruiter, no duplicate
  titles) including the edge case where no budget-owner exists in the pool
- integration: `contacts.company_id` FK integrity; CSV row count == selected
  contact count

**Pass criteria:** selection rule holds on 100% of a 10-company sample;
table UI sorts without error. **v0.1 exit gate (spec §12):** run for real —
115 companies, ~1,500 contacts fetched, ~300 selected, evidence populated.

---

## Phase 4 — Profile intake (stage [8]) · v0.2

**Builds:** `me_profile`/`projects` tables (new migration), GitHub/Devpost/
resume import, structured interview capture, versioning.

**Tests**
- unit: GitHub/resume parsers against fixtures
- integration: re-running intake after an edit creates a new `me_profile`
  version rather than overwriting

**Pass criteria:** profile + ≥5 real projects with one-liner/metric/tech
tags populated; version history intact after an edit.

---

## Phase 5 — Job postings + role inference (stages [3]/[4]) · v0.2

**Builds:** `job_postings` crawl, `role_profiles` derivation. Output must
drive **project selection**, not prose (§9.1 explicit warning — a
paragraph of "I see you need Postgres" is a machine tell).

**Tests**
- unit: stack/skill keywords → correct matched `project_ids` (fixture-based)
- integration: company with no intern postings falls back to full-time
  junior/mid inference

**Pass criteria:** `role_profiles` exist for ≥80% of Tier A/B companies;
every row has non-empty `derived_from`; output type is structured IDs, not
free text (enforced by schema, not eyeballed).

---

## Phase 6 — Draft engine + slop linter (stages [9]/[10]) · v0.2

**Builds:** `DraftProvider` interface, draft generation requiring
`evidence_ids[]`/`project_ids[]`, slop linter as a hard gate (banned
phrases + structural rules, §9.2).

**Tests**
- unit: one passing + one failing fixture per linter rule (word count,
  links≠1, em-dash>2, rule-of-three, "Not only" opener, no unique proper
  noun, duplicate first-5-words in batch, duplicate sentence structure)
- integration: a draft citing a non-existent `evidence_id` is rejected
  before reaching `pending` review status

**Pass criteria:** every linter rule has both fixtures green; 0% of
persisted drafts have an empty `evidence_ids[]`; slop score stored on 100%
of drafts.

---

## Phase 7 — Review UI (stage [11]) · v0.2

**Builds:** Send / Edit / Skip / Needs-work actions, evidence panel,
keyboard shortcuts (J/K/Enter/E/S/W), send-cap counter.

**Tests**
- component: each action dispatches the correct status transition
- component: Skip requires a reason code before submitting
- component: Send is disabled once today's cap is reached

**Pass criteria:** all 4 actions covered by passing component tests; cap
enforcement verified in test, not just visually.

---

## Phase 8 — Sending (stage [12]) · v0.2 · safety-critical

**Builds:** Gmail OAuth send (desktop flow, local token file), hard daily
cap with ramp (5/8/12/15), ≥4-day same-company stagger, plain-text only,
`message_id`/`thread_id` persistence.

**Tests**
- unit: cap boundary (15th send allowed, 16th blocked)
- unit: stagger boundary (exactly 4 days allowed, 3 days blocked)
- integration: mocked Gmail success/failure paths update `sends` correctly
- manual: one real send to the user's own inbox round-trips `message_id`/
  `thread_id`

**Pass criteria:** cap + stagger tests pass 100%, including both
boundaries; OAuth token never appears in logs or git history (grep check).
**No skipping this phase's tests to move faster — sending is the
irreversible action in this system.**

---

## Phase 9 — Reply watching + follow-ups (stages [13]/[14]) · v0.3 · ordering-critical

**Builds:** thread polling (15 min), reply classification (positive /
no-headcount / redirect / negative / auto-reply), immediate follow-up halt
on any reply, Needs Reply queue (4hr SLA), follow-up scheduler (D4/D10/D18).

**Tests**
- integration: reply recorded → scheduled follow-up for that contact is
  cancelled, run repeatedly (must be deterministic, zero flakiness)
- unit: one fixture per classification category
- unit: auto-reply/OOO does not count as a reply for halting or metrics

**Pass criteria:** reply-halts-followup test green on every run, no
exceptions. **Gate, not just a test:** this phase must ship and pass
before the first real follow-up is scheduled — never build follow-up
sending ahead of reply watching (spec §12 explicit ordering rule).

---

## Phase 10 — Analytics (stage [15]) · v0.3

**Builds:** funnel view (contacts→sent→delivered→replied→positive→
interview→final→offer), cuts (tier/size/location/title/day/slop score),
health counters (bounce rate, unactioned replies, cap usage, evidence gaps).

**Tests**
- unit: funnel counts against a hand-computed fixture dataset
- unit: bounce-rate alarm fires at >3% in a simulated dataset

**Pass criteria:** funnel numbers match the fixture exactly; alarm fires
in test.

---

## Phase 11 — End-to-end readiness (final product gate)

No new features — integration of everything above.

**Tests**
- one E2E smoke test: fixture scrape → evidence → contacts → rank → draft
  → lint → approve → send (mocked Gmail) → simulated reply → follow-up
  halt confirmed → analytics reflects it
- manual: 5 real emails sent end-to-end to an alternate inbox the user
  controls, including a simulated reply that correctly halts follow-ups

**Pass criteria:** E2E smoke test green; manual dry run confirms no step
requires babysitting. From here, "done" is defined by the spec's own pilot
gate (§6), not an engineering metric: **40 real emails sent, ≥8% reply →
scale as planned; 4–8% → one rewrite pass; <4% → stop and fix the message,
not the code.**

---

## Sequencing rules (non-negotiable, not phase-local)

- Phase 8 (send) cannot start until Phase 6 (linter) is green — no
  unlinted draft may ever reach a send call.
- Phase 9's reply watcher must ship and pass before any follow-up is
  scheduled, even in testing against a real inbox.
- Ranking (Phase 3) always precedes enrichment spend — never call
  `ContactProvider.enrich` on an unranked/unselected contact.
