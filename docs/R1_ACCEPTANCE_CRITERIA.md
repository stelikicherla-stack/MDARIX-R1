# MDARIX R1 Acceptance Criteria

## Status

PROPOSED for Day 1 architecture freeze.

## R1 Exit Criteria

- Product remains the core object.
- R1 remains system of intelligence, not system of record.
- Primary investigation journey is implemented end-to-end.
- Reality Investigation Brief is generated with evidence/provenance.
- Material AI claims are evidence grounded or labeled inference/hypothesis/unknown.
- Human review is required for material regulated decisions.
- AI provenance is recorded for material AI executions.
- Golden scenarios minimum 7/12 pass by R1 exit.
- Primary demo scenario passes.
- Critical defects are zero at release gate.
- Cross-tenant leakage is zero.

## Prohibited R1 Outcomes

- Unsupported causality claims
- Autonomous regulated decisions
- Hidden Neo4j dependency
- Generic chatbot workflow replacing the investigation lifecycle
- Complaint as highest-level business object
- Unknowns silently converted into assumptions
- Counterfactuals presented as predictions

## Primary Demo Acceptance

For the Product Rev D shutdown complaint scenario, MDARIX reconstructs timeline, retrieves evidence, maps Reality Graph relationships, generates competing hypotheses, identifies contradictions and unknowns, constructs a supported/hypothetical failure chain, explores a constrained scenario, and produces a Reality Investigation Brief that does not claim causality.
