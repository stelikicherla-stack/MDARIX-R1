# MDARIX R1 Retrieval Architecture

## Purpose

Day 9 establishes Trusted Evidence Retrieval. Retrieval finds relevant evidence; it does not decide truth, confidence, evidence strength, regulatory significance, or root cause.

## Boundaries

Retrieval operates over Day 8 `EvidenceChunk` records. It does not rechunk documents, create causal relationships, read Ground Truth answers, or replace deterministic lifecycle context.

## EvidenceChunk Indexing

`EvidenceChunk` is the primary semantic retrieval unit. Chunk embeddings are persisted in `evidence_chunk_embeddings` with tenant, evidence, chunk, checksum, embedding model, model version, dimension, pipeline version, status, and failure reason.

## Embedding Provider

R1 Day 9 uses `DeterministicEmbeddingProvider`, a local deterministic hash bag-of-words provider. It is explicit, versioned, reproducible, and suitable for controlled R1 validation without external secrets.

## pgvector

PostgreSQL 16 + pgvector stores vectors in `vector(32)`. The Day 9 migration creates an HNSW cosine index over indexed chunk embeddings.

## Structured Retrieval

Structured retrieval uses tenant-scoped canonical evidence metadata and `EvidenceEntityLink` lifecycle context such as Product, ProductVersion, Component, Supplier, LotBatch, Complaint, and Investigation.

## Semantic Retrieval

Semantic retrieval uses pgvector cosine distance over indexed chunk embeddings. Results are only candidates until tenant, lifecycle, temporal, and source-anchor validation pass.

## Hybrid Retrieval

Hybrid retrieval merges structured and semantic candidates, deduplicates by chunk, and boosts only when both mechanisms agree. Duplicate logical chunk results are collapsed.

## Ranking

Ranking is retrieval relevance only. It is not truth probability, confidence, causal probability, or evidence strength.

## Temporal Filters

`event` mode filters by evidence effective time. `known` mode filters by evidence ingestion/availability time and blocks future evidence leakage.

## Provenance

Each retrieval request creates a `retrieval_queries` row containing query text, filters, temporal mode, retrieval mode, embedding model, top K, returned refs, status, and timestamp.

## Failure Behavior

Embedding failures are recorded as `FAILED` rows and are not silently treated as indexed. No-match is a valid result with `NO_RELEVANT_EVIDENCE`.

## Limitations

Day 9 uses deterministic local embeddings for R1 validation. It is not an enterprise search benchmark and does not implement Day 10 investigation workspace behavior.
