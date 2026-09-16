# ADR-004: pgvector for Semantic Retrieval

## Context
R1 requires evidence and excerpt retrieval across investigation context.
## Decision
Use pgvector for semantic retrieval where justified.
## Rationale
pgvector runs in the verified PostgreSQL 16 foundation and avoids adding another storage service for R1.
## Consequences
Embedding metadata, model identity, evidence references, and retrieval evaluation are required.
## Alternatives Considered
External vector databases are deferred until scale or quality requirements prove need.
## Status
PROPOSED
