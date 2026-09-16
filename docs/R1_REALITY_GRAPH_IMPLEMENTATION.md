# MDARIX R1 Reality Graph Implementation

## Purpose

Day 6 implements the first executable MDARIX Reality Graph service. It exposes canonical lifecycle objects, supported relationships, temporal context, evidence references, and provenance through bounded service/API queries.

## Architecture

R1 remains PostgreSQL-first. The graph is a projection over canonical Day 2 tables, Day 5 source-canonical links, and Day 5 canonical relationships. No graph database or external cache is introduced.

## Node Model

Nodes expose controlled summaries:

- node ID
- entity type
- canonical entity ID
- tenant ID
- display label
- status/quality
- source count
- metadata summary

Raw source payloads and Ground Truth are not returned by basic graph endpoints.

## Relationship Model

Relationships have controlled semantic types, direction, assertion type, temporal fields, evidence count, provenance count, and safe metadata.

Assertion types:

- `SOURCE_ASSERTED`
- `DETERMINISTICALLY_DERIVED`

Day 6 does not create causal or hypothesized graph facts.

## Provenance And Evidence

Material relationships expose provenance through the relationship detail API. Evidence-backed relationships expose bounded evidence summaries, not full raw documents.

## Temporal Semantics

Relationships preserve effective and recorded timestamps where canonical data provides them. Historical product versions and lots remain separate graph nodes/relationships.

## Unresolved Relationships

Missing or unresolved relationships are not fabricated. For example, complaints without resolved lots do not receive complaint-to-lot edges.

## Traversal

Graph traversal is bounded. Default depth is small and maximum depth is controlled. Public APIs do not accept arbitrary graph query languages.

## Path Semantics

Paths mean relationship connectivity only. A graph path is not a causal path, root-cause finding, or failure chain.

## Tenant Isolation

All graph queries are scoped to the R1 synthetic tenant. Relationship validation checks endpoints under the same tenant.

## Ground Truth Isolation

The graph service reads canonical tables and staged source provenance. It does not read `evaluation/ground_truth/`.

## Day 7 Handoff

Day 7 may consume product graphs, investigation graphs, neighborhoods, paths, temporal relationship metadata, provenance, and evidence summaries for Product 360 and lifecycle timeline work.
