FIRST READ:
/docs/MASTER_CONTEXT.md

Before coding:
1. Read brief.md
2. Read architecture.md
3. Read api_contracts.md
4. Read db_schema.md
5. Read development_standards.md
6. Read codex_rules.md

Rules:
- Implement only the requested phase.
- Do not redesign architecture unless asked.
- Do not add new libraries without explaining why.
- Do not remove existing behavior unless instructed.
- Keep MVP lean.
- Prefer explicit, boring code.
- If unclear, leave a TODO and make the safest minimal assumption.
- After changes, summarize files changed and tests run.
- For any public-release sending/enrichment/generation work, enforce provider-safe request distribution:
  - async jobs instead of synchronous fan-out
  - per-user quotas
  - provider-level throttling (Gemini/Hunter/Gmail and future providers)
  - exponential backoff with jitter on 429/5xx
  - idempotency for send operations to avoid duplicates

Do not add dependencies unless:
- required for core functionality
- no lightweight native alternative exists
- dependency is actively maintained
- dependency significantly reduces implementation complexity

Do not refactor working code unless:
- bug exists
- duplication is severe
- architecture is blocked
- requested explicitly

Follow commit and PR standards defined in /docs/GIT_WORKFLOW.md

The rules in /docs/SYSTEM_INVARIANTS.md must NEVER break unless explicitly redesigned
