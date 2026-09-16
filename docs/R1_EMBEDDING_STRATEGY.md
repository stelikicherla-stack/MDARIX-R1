# MDARIX R1 Embedding Strategy

## Embedding Unit

The embedding unit is the trusted Day 8 `EvidenceChunk`.

## Model

Provider: `mdarix-deterministic`

Model: `mdarix-hash-bow-32`

Model version: `1.0`

Pipeline version: `R1-Day9`

## Dimension

Dimension: `32`

The dimension is explicit in code, schema, migration, indexing, validation, and reports.

## Distance Metric

Cosine distance through pgvector.

## Storage

Embeddings are stored in `evidence_chunk_embeddings` with tenant, evidence, chunk, chunk checksum, provider, model, model version, dimension, pipeline version, status, and failure reason.

## Indexing

The Day 9 migration creates a partial HNSW index for `INDEXED` embeddings.

## Versioning

Idempotency key:

- tenant
- chunk
- chunk checksum
- embedding model
- model version
- pipeline version

## Regeneration

If chunk checksum, model, model version, or pipeline version changes, a new embedding version is created. Historical embedding metadata is not silently overwritten.

## Failure Handling

Failed embedding generation records `indexing_status='FAILED'` and `failure_reason`. The chunk remains preserved.

## Security

Ground Truth evidence identifiers are excluded from indexing. Embeddings remain tenant-scoped and are never queried outside tenant context.
