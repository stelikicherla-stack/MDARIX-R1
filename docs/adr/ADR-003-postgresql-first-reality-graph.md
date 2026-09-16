# ADR-003: PostgreSQL-First Reality Graph

## Context
R1 needs graph-like relationships with provenance, evidence, and time.
## Decision
Use PostgreSQL-first relationship abstractions for the Reality Graph.
## Rationale
PostgreSQL is already verified, supports relational integrity and pgvector, and is sufficient for the initial vertical slice.
## Consequences
Graph storage remains abstracted so future graph databases can be evaluated without coupling business logic to them.
## Alternatives Considered
Neo4j on Day 1 was rejected as premature.
## Status
PROPOSED
