FIRST READ:
/docs/scoutreach-new.md

That document is the single source of truth for this project — strategy,
pipeline design, data model (§10), stack (§11), and build order (§12).
There is no separate architecture/API-contract/schema doc set: this is a
single-user, local-only Next.js app (SQLite + Drizzle, no backend service,
no auth, no multi-tenancy). Prior v1 docs describing a different
multi-tenant product are archived at /docs/archive/v1/ for reference only —
do not follow them.

Rules:
- Implement only the requested build-order phase (§12: v0.1 / v0.2 / v0.3).
- Do not add auth, multi-tenancy, or a hosted deployment — this is a local
  tool for one person for four months.
- Do not redesign the pipeline (§9) or data model (§10) unless asked.
- Do not add dependencies without explaining why.
- Keep it boring and explicit. Duplicate a few lines before adding an
  abstraction.
- If unclear, leave a TODO and make the safest minimal assumption.
- After changes, summarize files changed and tests run.
- Sending is safety-critical: hard daily cap (15/day), same-company stagger
  (>=4 days), reply-halts-followups is non-negotiable ordering (§9.5),
  email verification before send, bounce alarm at 3% (§9.4/§13).
- No draft may reach review without evidence_ids/project_ids tracing every
  factual claim to a stored row (§0.4, §9.1). No exceptions for speed.
