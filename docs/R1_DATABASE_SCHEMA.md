# MDARIX R1 Database Schema

## Purpose

The Day 2 schema establishes the executable PostgreSQL foundation for MDARIX R1. It implements tenant-aware, product-centered lifecycle investigation persistence without implementing product workflows, AI behavior, frontend screens, connectors, or the Golden Dataset.

## Schema Principles

- Product is the core lifecycle object.
- MDARIX is a system of intelligence, not a system of record.
- Source provenance is preserved.
- Time is first-class.
- Evidence, hypotheses, unknowns, and human decisions are distinct.
- AI output does not overwrite source facts or human decisions.
- Relationships carry provenance where materially relevant.
- Tenant isolation begins in the data model.

## Entity Groups

### Foundation

- `tenants`
- `source_records`
- `audit_events`
- `alembic_version`

### Product Lifecycle

- `products`
- `product_versions`
- `components`
- `suppliers`
- `manufacturing_sites`
- `lot_batches`
- `requirements`
- `changes`
- `risks`
- `failure_modes`
- `controls`

### Investigation

- `complaints`
- `investigations`
- `evidence`
- `hypotheses`
- `unknowns`
- `failure_chains`
- `failure_chain_nodes`
- `failure_chain_edges`
- `scenarios`
- `decisions`
- `ai_executions`
- `human_reviews`

### Relationships / Reality Graph

- `product_components`
- `product_suppliers`
- `component_suppliers`
- `lot_components`
- `investigation_complaints`
- `investigation_evidence`
- `hypothesis_evidence`
- `reality_relationships`

### Vector Foundation

- `evidence_embeddings`

## Tenant Model

Every tenant-owned domain table includes `tenant_id`. Composite foreign keys use `(tenant_id, id)` where cross-object relationships must stay within the same tenant. This prevents invalid cross-tenant attachments at the database level for core lifecycle relationships.

## Provenance Model

`source_records` captures source system, source record ID/version, raw payload reference, source/effective/ingestion timestamps, checksum, and data quality status. Source-derived tables can reference `source_records` and also retain source identifiers for query convenience.

## Temporal Model

The schema distinguishes source, event, effective, recorded, ingestion, created, updated, AI execution, review, and decision timestamps where semantically relevant. Day 2 tests verify effective and ingestion timestamps remain distinguishable.

## Evidence Model

`evidence` is first-class and includes evidence type, source references, document/extraction references, reliability status, fact type, content, and investigation linkage. `hypothesis_evidence` distinguishes `support` from `contradict`.

## Hypothesis Model

`hypotheses` are investigation-scoped and keep origin, status, reviewer disposition, and timestamps. Multiple hypotheses may coexist for an investigation.

## Unknown Model

`unknowns` are explicit investigation knowledge gaps. They are not represented merely as NULL fields.

## Failure Chain Model

`failure_chains`, `failure_chain_nodes`, and `failure_chain_edges` support ordered or graph-like causal paths. Edges can be `established_fact`, `hypothesized`, or `contradicted`.

## AI Execution Model

`ai_executions` stores provider/model metadata, prompt/orchestration versions, context/evidence references, tools invoked, structured input/output, rationale summary, uncertainty label, validation status, timestamp, latency, and error state. It does not store hidden chain-of-thought.

## Human Decision Separation

`decisions` captures authorized human decisions. `human_reviews` may reference AI executions and decisions, preserving the separation between AI recommendation and human authority.

## Audit Strategy

`audit_events` records tenant, actor, action, entity type, entity ID, correlation ID, details, and timestamp. Application services will emit audit events in later implementation days.

## JSONB Strategy

JSONB is used for structured AI inputs/outputs, evidence/context/tool references, audit details, scenario assumptions, and flexible provenance metadata. Canonical lifecycle fields remain relational columns.

## Vector Strategy

`evidence_embeddings` includes a pgvector `embedding vector(1536)` column, embedding model metadata, and evidence linkage. It has an HNSW cosine index for future semantic retrieval validation.

## Index Strategy

Indexes support tenant/product lookup, product-version lookup, component lookup, complaint temporal reconstruction, investigation/product lookup, evidence/investigation lookup, hypothesis evidence relation lookup, Reality Graph relationship traversal, and vector retrieval.

## Controlled Vocabulary Strategy

Day 2 uses CHECK constraints for high-risk semantics such as evidence fact type, hypothesis/evidence relationship type, AI/human/system origin, failure-chain edge status, and Reality Relationship assertion status. Broader controlled vocabularies can be promoted to reference tables later when Day 3+ fixtures define stable values.

## Inventory

See `docs/generated/R1_SCHEMA_INVENTORY.md` for the live schema inventory generated from PostgreSQL metadata.
