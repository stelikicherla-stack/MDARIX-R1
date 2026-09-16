# MDARIX R1 Investigation Workspace Implementation

## Purpose

The Day 10 Investigation Workspace assembles deterministic investigation context for a human investigator.

It presents:

- Investigation header
- Product and ProductVersion context
- Temporal context
- Reality Graph context
- Evidence records, chunks, source anchors, observations, and entity links
- Trusted retrieval context
- Limitations and guardrails

## Non-Goals

The workspace does not generate causality, confidence, regulatory significance, root-cause probability, or investigation disposition.

## Runtime Entry Point

API:

`GET /api/v1/investigations/{investigation_id}/workspace`

Query parameters:

- `temporal_mode`: `current`, `event`, or `known`
- `as_of`: optional timestamp
- `include_retrieval`: optional boolean
- `retrieval_top_k`: bounded retrieval result count

UI:

The Product 360 frontend includes an Investigation Workspace panel when investigation context is available. The panel shows deterministic workspace health, evidence context, retrieval status, temporal mode, limitations, and human-authority/causality guardrails.

## Data Sources

The workspace reads from existing R1 foundations:

- `investigations`
- `products`
- `product_versions`
- `complaints`
- `evidence`
- `evidence_chunks`
- `evidence_observations`
- `evidence_entity_links`
- `investigation_evidence`
- staged evidence metadata handoff records
- Product 360 service
- Reality Graph service
- Trusted Retrieval service

## Evidence Presentation

Evidence is shown only from tenant-scoped investigation context.

When a source evidence record exists but no materialized `EvidenceChunk` exists yet, the workspace creates a read-only fallback source anchor over preserved `evidence.content`. This fallback is labeled with `materialized=false` and reported as `MISSING_MATERIALIZED_CHUNKS`.

## Retrieval Semantics

Trusted retrieval is included as context only.

Retrieval rank means retrieval relevance only. It is not truth, confidence, evidence strength, causality, regulatory significance, or probability.

## Temporal Semantics

`event` mode filters by effective/event time.

`known` mode filters by ingestion/knowledge-available time and prevents future evidence leakage into historical known-as-of views.

## Guardrails

The workspace response explicitly states:

- Human authority is required
- Causality is not generated
- Ground Truth is not used
- Retrieval rank is contextual relevance only

## Validation

Day 10 validation:

`python infrastructure\database\scripts\day10_validate_investigation_workspace.py`

Automated tests:

`python -m pytest tests\test_day10_investigation_workspace.py -q --basetemp .pytest_tmp`

Frontend contract/build validation:

`npm.cmd run build`
