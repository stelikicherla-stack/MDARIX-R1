# MDARIX R1 Day 6 Reality Graph Contract

## Day 6 Inputs

Day 6 may rely on:

- Canonical lifecycle entities in Day 2 tables.
- Source-canonical links in `source_canonical_links`.
- Versioned identity rules in `identity_rules`.
- Canonical relationships in `canonical_relationships`.
- Temporal fields preserved on canonical entities and source records.
- Quality limitations and review-required links.
- Provenance and source-file references.

## Day 6 Responsibilities

Day 6 owns Reality Graph services and APIs, graph traversal, graph neighborhood responses, and API-facing graph contracts.

## Day 6 Must Preserve

- Source provenance.
- Relationship provenance.
- Temporal semantics.
- Contradictions and uncertainty.
- Human-review requirements.
- Ground Truth isolation.

## Day 6 Must Not Assume

- That Day 5 relationships imply causality.
- That unresolved identity is an error.
- That similar text means identical entities.
- That source systems were modified by MDARIX.
