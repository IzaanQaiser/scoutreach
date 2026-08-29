# Architecture

```text
React/Vite -> FastAPI -> Postgres
                 |          |
                 |          `-> durable DB-backed jobs
                 |-> source adapters
                 |-> Hunter/contact enrichment
                 |-> LLM adapter
                 `-> Gmail
```
