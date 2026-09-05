# Architecture

Browser (React)
    |
    | REST
    v
FastAPI API
    |
    +--> deterministic intelligence engine (demo)
    |
    +--> optional LLM provider adapter (future production layer)
    |
    +--> audit ledger (hash-linked JSON)
    |
    v
Structured decision object

Production evolution:
- PostgreSQL for incidents/users/audit events
- Redis for queues
- pgvector for incident knowledge retrieval
- OpenAI-compatible model gateway
- RBAC + SSO
- encrypted PII fields
- observability + evaluation suite
- human approval workflow
