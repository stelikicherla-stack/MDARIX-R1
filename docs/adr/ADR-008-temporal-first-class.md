# ADR-008: Temporal Data as First-Class Architecture

## Context
Investigations depend on what happened, when it happened, when it was recorded, and what was known at decision time.
## Decision
Temporal reality is first-class in R1.
## Rationale
MDARIX must distinguish source, event, effective, recorded, ingestion, investigation, AI execution, and decision timestamps.
## Consequences
APIs, database fields, graph relationships, and briefs must preserve temporal semantics.
## Alternatives Considered
Using only `created_at` and `updated_at` was rejected.
## Status
PROPOSED
