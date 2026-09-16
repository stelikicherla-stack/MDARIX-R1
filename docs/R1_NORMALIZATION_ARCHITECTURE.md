# MDARIX R1 Normalization Architecture

## Purpose

Day 5 converts immutable staged source records into controlled canonical lifecycle identities while preserving source truth.

## Boundary

Day 5 performs structural normalization, deterministic identity resolution, canonical table mapping, source-canonical linking, relationship resolution, quality propagation, ambiguity handling, and Day 6 handoff preparation.

Day 5 does not build Reality Graph APIs, graph visualization, Product 360 UI, Timeline UI, AI Investigator, hypothesis generation, root-cause reasoning, or causal graph services.

## Pipeline

STAGED SOURCE RECORD -> FIELD NORMALIZATION -> IDENTIFIER NORMALIZATION -> CONTROLLED VOCABULARY NORMALIZATION -> TEMPORAL NORMALIZATION -> CANDIDATE GENERATION -> DETERMINISTIC RULE EVALUATION -> CANONICAL UPSERT -> SOURCE-CANONICAL LINK -> RELATIONSHIP RESOLUTION -> PROVENANCE -> VALIDATION.

## Source Preservation

`staged_source_records.raw_payload`, `parsed_payload`, source timestamps, checksums, source files, and quality issues remain immutable Day 4 input history. Day 5 stores normalized comparison values in `source_canonical_links` and does not replace source values.

## Identity Model

Canonical entities use MDARIX UUID primary keys. Business identifiers and source identifiers remain distinct.

Day 5 adds:

- `normalization_runs`
- `identity_rules`
- `source_canonical_links`
- `canonical_relationships`
- `normalization_issues`

## Resolution Outcomes

- `MATCHED`
- `NEW_CANONICAL_OBJECT`
- `AMBIGUOUS`
- `UNRESOLVED`
- `CONFLICT`
- `REQUIRES_HUMAN_REVIEW`

## Rule Strategy

Resolution is deterministic-first. Rules are versioned in `ingestion/normalization/rules/identity_rules.json` and persisted in `identity_rules`.

Rule precedence favors exact identifiers and composite identity over aliases. Similarity alone never creates authoritative identity.

## Canonical Value Selection

Canonical values come from controlled source fields with deterministic rules. For product versions, source forms such as `Rev D`, `PRD100 Rev D`, and `Product-100 / Revision C` are normalized only for comparison while source strings remain preserved.

## Quality And Human Review

Duplicate candidates, incomplete traceability, missing lots, and uncertain evidence are retained as warnings or review-required outcomes. Day 5 treats unresolved identity as safer than a false merge.

## Relationship Resolution

Day 5 creates supported lifecycle relationships such as lot-to-product-version and component-to-supplier. It does not create causal relationships.

## Ground Truth Isolation

Application normalization reads `staged_source_records` only. `evaluation/ground_truth/` is not imported by the normalization service and appears only in tests/evaluation.

## Idempotency

Canonical writes use deterministic keys and conflict-safe updates. Re-running normalization does not duplicate canonical objects.

## Day 6 Handoff

Day 6 receives canonical entities, canonical relationships, source-canonical links, temporal fields, quality limitations, and provenance for Reality Graph services and APIs.
