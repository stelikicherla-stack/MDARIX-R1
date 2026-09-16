# MDARIX R1 Reality Graph Specification

## Status

PROPOSED for Day 1 architecture freeze.

## Definition

The MDARIX Reality Graph represents objects, relationships, time, evidence, and contradictions.

## Graph Objects

Product -> Product Version -> Component -> Supplier -> Manufacturing Site -> Lot -> Complaint -> Investigation -> Failure Mode -> Risk -> Evidence -> Hypothesis -> Decision.

## Relationship Requirements

Relationships may require source, confidence, effective date, recorded date, provenance, and evidence reference. Unsupported edges must not be treated as facts.

## PostgreSQL-First Decision

R1 uses PostgreSQL relational tables plus explicit relationship abstractions. pgvector supports semantic retrieval where justified. Neo4j is not introduced on Day 1.

Business logic must use graph service abstractions so storage can evolve later without changing product workflows.

## Contradictions

Contradictions are first-class relationship annotations. A graph path may be plausible, contradicted, partially supported, or hypothetical.

## Primary Example Validation

The graph must represent Supplier Process Change -> Component Rev B -> Product Rev D configuration -> affected lots -> shutdown complaints -> increased complaint frequency, while preserving contradictions such as pre-Rev B complaints and passed validation testing.
