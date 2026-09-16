# ADR-002: Product as Core Object

## Context
Complaints are important, but medical-device decisions ultimately concern product reality.
## Decision
Product is the core R1 business object.
## Rationale
Complaints, investigations, risks, components, suppliers, lots, evidence, hypotheses, and decisions must connect to products and product versions.
## Consequences
Domain, UI, graph, API, and database contracts are product-centered.
## Alternatives Considered
Complaint-centered architecture was rejected because it narrows lifecycle reasoning.
## Status
PROPOSED
