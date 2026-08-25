# Scoutreach v2 — Strategy + System Spec

**Goal:** one signed offer for a full-time software co-op, Jan 11 – Apr 30 2027, at a startup.
**Owner:** Izaan Qaiser · **v2 written:** Aug 25 2026 · **Offer in hand by:** Dec 19 2026
**Supersedes:** Scoutreach Plan & Spec v1

> Dates assume a Waterloo-style Winter 2027 term (Jan 11 – Apr 30 2027). Swap in your actual term dates — they appear in every template.

---

# Part 0 — What v2 changes, and why

v1 was the campaign. v2 is the campaign plus the machine that runs it. Six things had to change on contact with the tooling idea.

### 0.1 The Snap email is survivorship bias. Keep the form, drop the expectation.

That email worked because of four things, and brevity was the least of them: it went **to Evan Spiegel personally**, in **2014**, from a **high-school junior** (novelty, and the thing that made it forwardable), at a company small enough that the founder read his own inbox. You are seeing the one that worked. The identical email sent to 300 people in 2026 is a rounding error above zero.

Notice what that email does *not* contain: a single word about Snapchat. In 2014 that was fine. In 2026, when every inbox takes 30+ AI-written cold emails a day, "short and punchy with nothing specific in it" is precisely the shape of the thing people delete without reading.

**So: adopt the constraint, invert the content.** Under 120 words, no preamble, one ask — yes, all of that. But the words you save on pleasantries get spent on *one verifiable specific about them*. Short is the form. Specific is the payload. A tool that generates short generic emails at scale is a tool for burning 115 companies efficiently.

### 0.2 10–20 contacts per company would end the campaign. Store many, send few.

This is the one place I'd overrule you outright. Fifteen emails into a 40-person startup is not outreach — it is a mailbomb, and the failure is not "low reply rate," it's the domain-level spam complaint and the Slack thread where someone pastes your email and says "this guy hit all of us."

But the underlying instinct is right, and the good news from the API research (§0.3) is that **collecting is free while sending is expensive.** So the pipeline splits:

- **Fetch** 10–25 people per company — free, 0 credits, gives the ranker something to work with
- **Rank** them (§8.3)
- **Draft and send to the top 2–4**, by headcount band, per v1 §4
- Keep the rest in the DB as a bench — for the second wave, for when someone leaves, for when a reply redirects you

You get your breadth. The campaign keeps its reputation.

### 0.3 Apollo API — verified, and it's better than expected

| Endpoint | Returns emails? | Credit cost | Notes |
|---|---|---|---|
| **People Search** (`/people/search`) | **No** — explicitly "doesn't return email addresses or phone numbers" | **0 credits** | Free to enumerate every engineer at every company. Cap: 50k records, 100/page, 500 pages |
| **People Enrichment** (`/people/match`) | Yes, with `reveal_personal_emails=true` | **1 credit** for email/demographics (+8 only if a mobile number is returned — **don't request phones**) | This is the only step that costs you |

Free-plan API access exists but **requires the account be registered with a work email address**. Rate limits, free plan: **50/min, 200/hr, 600/day** — far above what you need (~115 search calls + ~300 enrichment calls, total).

**One thing to verify before you write the enrichment code:** whether API enrichment draws from the *email credit* pool (10,000/mo on free) or the *export credit* pool (120/**year** on free). The docs don't say; your billing page does — Settings → Billing and credits, and Settings → Integrations → API Keys → Usage. If it's export credits, free tier gets you 120 emails total for the year and you buy one month of Basic (~$49, 12,000 export credits) and pull everything in one sitting. **Build the enricher behind an interface so you can swap in pattern-inference + verification if the credit math comes back bad.**

### 0.4 The real risk isn't throughput. It's that the output reads like a machine wrote it.

Every founder you're emailing gets AI cold email daily and has a trained ear for it. The tells are specific and the tool must be built to avoid them structurally, not by asking a model nicely:

- **Evidence-linked personalization is a hard gate.** No draft reaches your review queue unless every factual claim about the company maps to a stored row with a source URL and the exact snippet it came from. One hallucinated fact about someone's product is instantly disqualifying, and it is the single most likely way this tool embarrasses you.
- **A slop linter blocks send** (§9.2). Banned phrases, word count, link count, em-dash count, structural repetition.
- **The model drafts the scaffold; you write or rewrite the specific line.** The tool's job is research, retrieval, selection, and logistics — not final prose. This is the difference between "AI wrote 300 emails" and "you wrote 300 emails 8× faster."

### 0.5 Reject-then-batch-edit is the wrong queue design

By the time you're editing yesterday's rejects, you've lost the company context you had loaded when you rejected it — you'll re-read the evidence panel to make a two-word fix. Three actions instead:

- **Send** — goes now (subject to daily cap)
- **Edit** — inline, right there, then send. Most "rejects" are one bad sentence
- **Skip** — kill this contact, with a reason code (`bad_fit`, `no_evidence`, `wrong_person`, `company_dead`). Reason codes are what tell you *which pipeline stage* is underperforming

Keep a `needs_work` bucket for the genuine "I need to go build something for this company first" case — that's Tier A, and it's a different workflow, not a queue.

### 0.6 Six things missing from your spec, one of them large

1. **Follow-ups.** Day 4 / 10 / 18, threaded. This roughly doubles reply rate and it is *more* valuable than the initial-draft feature. It was absent entirely.
2. **Reply detection.** If someone replies and your tool sends follow-up #2, you've undone the win. Non-negotiable, and it must be built before any follow-up is scheduled.
3. **Email verification before send.** Bounces above ~3% damage sender reputation for everything after.
4. **Dedupe.** Same human at two companies, re-scrapes, contacts who changed jobs.
5. **Same-company stagger.** Enforced in software: minimum 4 days between two contacts at one company.
6. **A hard daily send cap.** An approve/send UI makes it frictionless to fire 60 in one sitting, which wrecks both deliverability and per-email judgment. Cap at 15/day, warn at 10.

### 0.7 Scope: the tool must not eat the campaign

Sep 15 is the pilot date and it does not move. If v0.2 isn't running by Sep 14, you run the pilot out of a spreadsheet and keep building. Build order in §12 is sequenced so that every week produces something usable on its own.

---

# Part I — Strategy

## 1. Funnel math

| Stage | Rate | Needed |
|---|---|---|
| Offer from final round | 30% | 3–4 finals |
| First interview → final | 50% | 7 first interviews |
| Positive reply → interview | 50% | 14 positive replies |
| Reply → positive (vs. "no headcount") | 40% | 35 replies |
| Contact → reply (personalized + 3 follow-ups) | 12% | **~290 contacts** |
| Contacts per company (avg 2.5) | — | **~115 companies** |

**~115 companies · ~290 first-touch emails · ~800 sends including follow-ups · ~12/day over 13 weeks.**

The tool changes the *cost per company*, not the arithmetic. If it works, the right response is more Tier B companies at the same personalization depth — not more contacts per company (§0.2), and not thinner personalization.

*Every rate above is a guess. The Oct 3 gate replaces them with yours.*

## 2. Targeting

**Primary source: topstartups.io.** Filters: funding stage (Pre-Seed → Series I), HQ city/country, industry (22 categories), company size (8 bands), founded year, investor. No CSV export or public API — hence §7.1.

**Filter settings:** size 11–50 and 51–200 · stage Seed / Series A / Series B · location SF Bay, NYC, Toronto, Remote · industry: 4–6 you can speak to credibly.

**Size beats stage.** You need a company where one person can say yes without an ATS and a req. That's headcount 11–200. Keep Series A+ as a quality signal; make headcount the hard filter.

**Secondary sources (~30% of list),** so you're not fishing the same pond as everyone else who found topstartups.io: YC Work at a Startup · topstartups.io/jobs · companies that raised in the last 90 days · portfolio pages of 5–10 funds.

**Quality bar — all four:**
1. 11–200 employees
2. Raised within ~24 months
3. You can name their product and its buyer in one sentence
4. **Has a public engineering surface** — blog, changelog, docs, OSS repo, or a product you can sign up for

Rule 4 is now machine-enforced: no evidence rows → the company can't produce a draft → it gets auto-flagged for manual review or cut. This is the guardrail that keeps the tool from generating generic email at scale.

**Target: 115 companies by Sep 12.**

## 3. Contact selection

| Company size | Send to | Who |
|---|---|---|
| 11–50 | 2 | CTO or technical co-founder, + 1 senior/staff engineer |
| 51–120 | 3 | VP Eng / Head of Eng, + 1 EM, + 1 senior engineer |
| 121–200 | 3–4 | Add a technical recruiter or Head of Talent |

Fetch 10–25, send to these. Budget-owner first, then an engineer whose work you can speak to. Never `hiring@` or `careers@`. Minimum 4 days between two contacts at the same company.

## 4. Tiering

| Tier | Companies | Effort each | Contacts | Emails | What makes it different |
|---|---|---|---|---|---|
| **A** | 15 | 60–90 min | 3 | 45 | You build or record something *for them*. Tool assists; you do the work |
| **B** | 50 | 15 min | 3 | 150 | Tool-drafted from real evidence; you rewrite line 1 |
| **C** | 50 | 4 min | 2 | 100 | Tool-drafted, you approve or one-line edit |

≈295 first-touch emails. **Run Tier C first as the pilot** — worst copy hits least-important companies.

Tier A is the only tier that's hard for another student with the same tool to copy. Protect its time budget; if the tool saves you hours on B and C, spend them on A.

## 5. The email

**Constraints:** ≤120 words · plain text · **one** link · one ask · no attachments, images, HTML signature, or tracking pixel.

**Structure:**
1. Proof you know them — specific, verifiable, sourced
2. Who you are + the single most impressive concrete thing you've shipped (one project, with a number)
3. The ask, made easy — dates, availability, work-auth answer
4. One link
5. A soft question answerable in one line

**Make the ask cheap to answer.** "Is there anyone on the team who takes co-op students?" costs them a name. "Would you hire me?" costs them a decision.

**Subject lines** — never "Internship Inquiry":
`built [thing] with [their product] — free Jan–Apr` · `[University] CS — question about winter interns` · `re: [specific changelog item]`

### Tier C template

> Subject: [University] CS student — winter co-op question
>
> Hi [Name] — saw [specific sourced detail].
>
> I'm a [year] CS student at [University]. Most recently I built [project] — [one line with a concrete number]. I'm free full-time Jan 11 – Apr 30, looking for somewhere small enough that I'd own real work.
>
> Everything I've built, with demos: [one link]
>
> Is there anyone on the team who takes on co-op students? Happy to be pointed elsewhere.
>
> — Izaan

### Tier A template

> Subject: built [thing] on top of [their product]
>
> Hi [Name] — I've been using [product] for [real use case]. [One sentence of specific, credible observation.]
>
> I built [the thing] against it over the weekend — [what it does in 8 words]. 90-second demo: [one link]
>
> I'm a [year] CS student, free full-time Jan 11 – Apr 30. I'd like to spend it at [company].
>
> Worth a 15-minute call?
>
> — Izaan

**Follow-ups: Day 4 / 10 / 18,** threaded in your own thread. Each must add something new — a shipped project, a new demo, a thought on something they announced. Never "just bumping." Then stop: four touches is the line.

## 6. Calendar

| Window | Phase | Campaign | Tool |
|---|---|---|---|
| **Aug 25 – Sep 5** | Build | Landing page, 3 demo videos, repo cleanup, inbox warmup | **v0.1** — scraper, DB, contact fetch + rank, evidence crawl |
| **Sep 6 – Sep 14** | Build | Profile intake session, Tier A list, work-auth answer confirmed | **v0.2** — draft engine, slop linter, review UI, Gmail send |
| **Sep 15 – Oct 3** | **Pilot** | 40 Tier C emails + follow-ups. Measure. Rewrite copy | **v0.3** — follow-up scheduler, reply watcher, analytics |
| **Oct 6 – Nov 21** | Main push | Tier B then A. ~6 first-touches/day, ~15 sends/day | Hardening, second-wave logic |
| **Nov 24 – Dec 19** | Close | Convert conversations, run interviews, second wave | — |
| **Dec 22 – Jan 8** | Late wave | The "we need someone in two weeks" window. Only if unsigned | — |

**Pilot gate, Oct 3.** After 40 emails + follow-ups:
- **≥8% reply** → scale as planned
- **4–8%** → one rewrite pass, 20 more, re-measure
- **<4%** → **stop.** The problem is the email or the landing page. Sending 250 more of a message that doesn't work just burns the list

The gate is a feature, not a note — the tool should refuse to release Tier B drafts until you've entered pilot results.

## 7. Work authorization — resolve before any US email

If you're Canadian targeting US startups, this silently kills more replies than bad copy. A 30-person startup reads "international student" as lawyers and cost, and passes without asking.

**Confirm with your co-op office what you're actually eligible for** (many co-op programs sponsor J-1 at no cost or paperwork to the employer), then put it in one clause:

> "I'm eligible to work in the US through my university's program — no sponsorship, cost, or paperwork on your side."

Store it as a profile field so it renders into every US draft automatically. If it turns out not to be true, add a `can_hire_me` flag on companies and weight the list to Toronto and remote-friendly.

## 8. Other channels — 30% of effort

- **Boards where a posting proves budget** — topstartups.io/jobs, YC Work at a Startup. Apply *and* email a human at the same company.
- **Your co-op portal**, in parallel. An offer there is a floor under all of this, and it makes you negotiate better.
- **Warm intros.** Ask every positive reply: *"if there's no room on your team, is there another team or company you'd point me at?"* Referrals convert at multiples of cold — the tool should have a one-key "log a referral" that creates a pre-warmed contact.

---

# Part II — The System

## 9. Pipeline

```
[1] Scrape companies      topstartups.io + secondary → companies
        ↓
[2] Evidence crawl        blog / changelog / docs / repos / news → company_evidence
        ↓
[3] Job posting crawl     intern + full-time postings → job_postings
        ↓
[4] Role inference        what an intern would actually do here → role_profiles
        ↓
[5] Contact fetch         Apollo People Search (0 credits) → contacts (10–25/co)
        ↓
[6] Rank + select         score, pick 2–4 by headcount band → contacts.selected
        ↓
[7] Email + verify        Apollo Enrichment (1 credit) → verify → contacts.email_status
        ↓
[8] Profile intake        one-time Q&A + GitHub/Devpost/resume import → me_profile, projects
        ↓
[9] Draft                 evidence + role_profile + matched projects → drafts
        ↓
[10] Slop lint            block on violation → drafts.lint_result
        ↓
[11] Review               Send / Edit / Skip / Needs-work
        ↓
[12] Send                 Gmail API, plain text, daily cap, stagger → sends
        ↓
[13] Watch                poll threads for replies → replies; halt follow-ups
        ↓
[14] Follow up            D4 / D10 / D18, threaded, only if no reply
        ↓
[15] Analytics            funnel vs. §1 targets
```

Every stage is independently runnable and idempotent. You will re-run stage 2 a lot.

### 9.1 Stage notes

**[1] Scraper.** Check the network tab before writing a DOM parser — the site is very likely Airtable-backed and calling a JSON endpoint the frontend hits is more stable and an order of magnitude less code. Respect robots.txt and ToS, rate-limit to ~1 req/2s, cache raw responses to disk so re-runs cost nothing. Store `raw_json` alongside parsed fields; the parser will be wrong twice before it's right.

**[2] Evidence crawl.** For each company: fetch `/blog`, `/changelog`, `/docs`, `/careers`, `/engineering`, GitHub org, and recent news. Store **URL + title + exact snippet + retrieved_at** per item. This table is the campaign's spine — no evidence, no draft. Target 3–8 rows per company.

**[3] + [4] Role inference.** Good idea, easy to misuse. Search for the company's intern postings first; if none, infer from full-time junior/mid postings. **The output should drive project *selection*, not prose.** A paragraph of "I see you're looking for someone with Postgres and React experience" reads like a machine. The right use is: this company's stack is X, therefore of Izaan's 9 projects, mention #4. Store `required_skills[]`, `stack[]`, `likely_intern_work` (internal-only text), `confidence`, `derived_from[]`.

**[5] Contact fetch.** People Search, 0 credits. Filter `person_titles` on engineering + leadership + talent. Pull 10–25. Free-tier limits (600/day) are not a constraint.

**[6] Ranking.**

```
score = title_weight
      + 15 if department matches your strongest project's domain
      + 10 if tenure > 12 months     (new hires don't own headcount)
      +  8 if public footprint exists (GitHub, blog, talks — gives you a hook)
      -  20 if title is recruiter AND headcount < 120

title_weight:  CTO / technical co-founder      100
               VP Eng / Head of Engineering      90
               Director of Engineering           80
               Engineering Manager               70
               Staff / Principal Engineer        65
               Senior Engineer                   55
               Technical recruiter / Head Talent 40
               Junior / mid IC                   20
```

Selection: top N for the headcount band, **must include ≥1 budget-owner**, **at most 1 recruiter**, no two with identical titles.

**[7] Email + verify.** Enrichment with `reveal_personal_emails=true`, **never `reveal_phone_number`** (8 credits, useless to you). Behind an interface — fallback is `firstname@domain` pattern inference confirmed against one known-good address per domain. Verify everything before send; drop anything `invalid`, hold `risky` for manual review. Keep bounce rate under 3%.

**[8] Profile intake.** A structured interview, not a chat log. Import GitHub (repos, languages, commit recency, READMEs), Devpost (projects, awards), resume PDF, and the landing page. Then ask the questions imports can't answer:

- For each project: what was the hardest technical decision, and what did you pick? What's the number that makes it real (users, latency, scale, accuracy)? What broke, and how did you find out?
- What do you want to be doing in four months?
- What are you not good at yet? *(This one produces the most credible line in any cold email.)*

Output: a versioned `me_profile` + `projects` table with one-liners, metrics, tech tags, links, and a story per project. **Editable, and re-runnable as you ship things** — you'll add two projects before December.

**[9] Draft.** Inputs: contact, company, top-3 evidence rows, role_profile, 1–2 matched projects, tier, template, work-auth clause. Output: subject, body, **plus `evidence_ids[]` and `project_ids[]` used**. A draft that cites no evidence row cannot enter review. For Tier A, the tool produces the research brief and a skeleton — you write it.

### 9.2 Slop linter — blocks send, not a warning

**Banned phrases** (case-insensitive): `hope this email finds you well` · `I came across` · `I was impressed by` · `I'd love to` / `would love the opportunity` · `passionate about` · `reach out` · `leverage` · `utilize` · `delve` · `robust` · `seamless` · `cutting-edge` · `game-chang` · `your innovative approach` · `in today's` · `truly` · `excited to see`

**Structural rules:**
- Word count > 120 → block
- Links ≠ 1 → block
- Em-dashes > 2 → block
- Rule-of-three parallel list → block *(the single loudest AI tell)*
- Sentence starting "Not only" → block
- Personalization line contains no proper noun unique to the company → block
- Body shares its first 5 words with any other draft in the batch → block
- Two drafts to the same company with identical sentence-count structure → block

Show a **slop score** in the review UI and store it. At the Oct 3 gate, check slop score against reply rate — if there's no correlation, relax the rules; if there is, tighten them.

### 9.3 Review UI

Left: the draft, editable in place. Right, always visible: contact card · company one-liner · **evidence rows with source links and snippets, with the one cited in the draft highlighted** · inferred intern work · which projects were selected and why · slop score · send-cap counter for today.

Keyboard: `J`/`K` navigate · `Enter` send · `E` edit · `S` skip (prompts for reason) · `W` needs-work.

The evidence panel is the point. You should be able to confirm the personalized claim is true in about three seconds without leaving the screen. If you can't, that's a `skip` with reason `no_evidence`, and it's telling you stage 2 needs work on that company.

### 9.4 Sending

Gmail API with OAuth (not SMTP — API sends look native and inherit your account's reputation). `text/plain` only. Store `message_id` and `thread_id` for threading.

Hard rules, enforced in code:
- **Max 15 sends/day**, warn at 10. Ramp: 5/day week 1, 8 week 2, 12 week 3, 15 after
- **≥4 days between contacts at the same company**
- Tue–Thu, 8:00–10:30 recipient-local, jittered ±20 min
- No pixel, no link tracking, no auto-added signature block

### 9.5 Reply watching

Poll tracked `thread_id`s every 15 minutes. On any inbound message:
- **Halt all scheduled follow-ups for that contact immediately** — this is the most important line in the spec
- Classify: `positive` / `no-headcount` / `redirect` / `negative` / `auto-reply`
- **`negative` or `no-headcount` → pause every other contact at that company** pending your review. One "we're not hiring" means the company is answered; a second email from you after that is the bad kind of memorable
- **`redirect` → one-key "create contact from referral"**, pre-marked warm
- Surface in a **Needs Reply** queue with a 4-hour SLA timer. An unactioned reply is the most expensive failure in this system

Auto-replies and OOO must not count as replies for follow-up-halting *or* for your reply-rate metric.

### 9.6 Analytics

Funnel vs. §1 targets, live: contacts → sent → delivered → replied → positive → interview → final → offer.

Cuts: by tier · by company size · by location · by title band · by day-of-week · by slop score.

Health counters, always visible: bounce rate (alarm >3%) · unactioned replies (**must be 0**) · today's sends vs. cap · scheduled follow-ups next 7 days · companies with zero evidence rows.

One weekly view for the Friday 20-minute review. **If Tier A's reply rate isn't beating Tier C's, personalization isn't landing** — and the fix is the content of line 1, not more volume.

## 10. Data model

```
companies          id · name · domain · url · stage · size_band · headcount · location ·
                   industry · description · last_funding_date · investors[] · source ·
                   tier · status · why_them · can_hire_me · raw_json · scraped_at

company_evidence   id · company_id · kind(blog|changelog|docs|repo|posting|news) ·
                   url · title · snippet · retrieved_at

job_postings       id · company_id · title · is_intern · url · raw_text ·
                   parsed_skills[] · parsed_responsibilities[] · retrieved_at

role_profiles      id · company_id · likely_intern_work · required_skills[] · stack[] ·
                   derived_from[] · confidence

contacts           id · company_id · apollo_id · first · last · title · seniority ·
                   department · linkedin · tenure_months · email · email_status ·
                   email_source · rank_score · selected · skip_reason · created_at

me_profile         id · version · university · year · term_start · term_end ·
                   work_auth_clause · link · created_at

projects           id · name · one_liner · metric · tech[] · domain · links[] ·
                   hard_decision · story · demo_url · active

drafts             id · contact_id · tier · subject · body · evidence_ids[] ·
                   project_ids[] · slop_score · lint_result ·
                   status(pending|edited|approved|skipped|needs_work|sent) · created_at

sends              id · draft_id · gmail_message_id · gmail_thread_id · sent_at

followups          id · contact_id · thread_id · seq(1|2|3) · scheduled_for ·
                   body · status(scheduled|sent|cancelled)

replies            id · contact_id · thread_id · received_at · classification ·
                   snippet · actioned_at

events             id · entity · entity_id · type · payload · at        (append-only)
```

`events` is append-only and cheap. It's how you reconstruct what happened in November when the numbers look wrong.

## 11. Stack

Boring on purpose — one user, runs locally, no auth to build.

- **Next.js** (App Router), single-user, localhost
- **SQLite + Drizzle** — one file, trivially backed up, no Postgres to run
- **Playwright** for scraping (already what you'd want for a JS-rendered site)
- **Gmail API** via OAuth desktop flow, token in a local file
- **Apollo REST** behind a `ContactProvider` interface so the enrichment source is swappable
- Model calls behind a `DraftProvider` interface — you'll switch models at least once
- **BullMQ or a plain cron table in SQLite** for follow-up scheduling. Prefer the cron table; you don't need Redis for 800 emails

Don't build auth, multi-tenancy, or a hosted deployment. It's a local tool for one person for four months.

## 12. Build order

Each week ships something usable alone. **If a week slips, the campaign continues without that week's feature.**

**v0.1 — Aug 26 – Sep 5.** Scraper → DB → evidence crawl → Apollo search + rank → export CSV. No UI beyond a sortable table. *Output: 115 companies, ~1,500 contacts, ~300 selected, evidence rows populated.* This alone makes the spreadsheet plan work.

**v0.2 — Sep 6 – Sep 14.** Profile intake, job-posting crawl + role inference, draft engine, slop linter, review UI, Gmail send with cap and stagger. *Output: you can review and send.*

**v0.3 — Sep 15 – Sep 26.** Follow-up scheduler, reply watcher, Needs Reply queue, analytics. *Built while the pilot runs on v0.2.* Follow-up #1 for pilot emails isn't due until Day 4, so this is genuinely parallelizable — but reply watching must ship **before** the first follow-up fires.

**Hard rule:** if v0.2 isn't running Sep 14, the pilot runs from a spreadsheet on Sep 15 anyway. The tool serves the campaign.

## 13. Risks

| Risk | Mitigation |
|---|---|
| Drafts read as AI → reply rate near zero | Evidence gate + slop linter + you write line 1. Pilot gate catches it at 40 emails, not 300 |
| Hallucinated fact about a company | Every claim traceable to a stored snippet; evidence panel next to draft; skip if unverifiable |
| Apollo credits are export credits (120/yr free) | Verify in billing *before* building. Swappable provider; fallback is pattern inference + verification |
| Domain/IP reputation damage | 15/day cap, ramp schedule, verify before send, bounce alarm at 3%, plain text, one link |
| Auto follow-up after someone replied | Reply watcher ships before the first follow-up fires. Non-negotiable ordering |
| Tool eats the campaign | v0.1 alone makes the spreadsheet plan work. Sep 15 doesn't move |
| topstartups.io ToS / rate limiting | robots.txt, 1 req/2s, cache raw responses, personal use only, no redistribution |
| Sending law (CASL in Canada, CAN-SPAM in US) | Both carve out room for genuine non-commercial job inquiries — CASL has an exemption for messages that are an inquiry or application related to employment. Worth 20 minutes confirming for your situation; I'm not a lawyer, and this is not legal advice |

## 14. Open items

- [ ] **Verify Apollo credit pool** (email credits vs. export credits for API enrichment) — Settings → Billing and credits. Blocks stage 7 design
- [ ] Register the Apollo account with a **work/edu email** — free-tier API access requires it
- [ ] Confirm US work authorization path with co-op office — blocks all US outreach
- [ ] Check topstartups.io network tab for a JSON endpoint before writing a DOM parser
- [ ] Pick the 4–6 industries you can speak to credibly
- [ ] Choose sending inbox: .edu vs. personal domain (if domain, buy and warm **this week**)
- [ ] Draft the 15-company Tier A list — it decides what you build in September
- [ ] Decide: does the landing page get its own domain, and does it need to be live before Sep 15? (Yes)

---

*Living doc. Revise §1's rates against actuals at the Oct 3 gate, and re-tune the slop linter against the slop-score/reply-rate correlation at the same time.*