# ADR-005: Single Controlled AI Orchestrator for R1

## Context
R1 needs AI support without uncontrolled multi-agent behavior.
## Decision
Use one controlled AI orchestrator with logical specialists/tools.
## Rationale
This preserves auditability, reproducibility, scope control, and human review.
## Consequences
Specialists are service/tool boundaries, not independently autonomous agents.
## Alternatives Considered
An unrestricted multi-agent swarm was rejected as unnecessary and unsafe for R1.
## Status
PROPOSED
