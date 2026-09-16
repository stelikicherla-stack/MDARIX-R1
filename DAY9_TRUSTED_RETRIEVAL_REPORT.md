# MDARIX R1 Day 9 Trusted Evidence Retrieval Report

## 1. Day 9 Status

PASS locally; remote push pending explicit approval.

## 2. Entry Gate

Day 0-Day 7: PASS. Week 1 Review: PASS. Day 8 Evidence Intelligence: PASS.

## 3. Day 8 Readiness

Day 8 provided preserved evidence, chunks, observations, source anchors, entity links, and AI provenance. Day 9 indexes Day 8 chunks and does not rechunk documents inside retrieval.

## 4. Retrieval Architecture

Implemented tenant-scoped trusted retrieval with structured, semantic, and hybrid modes.

## 5. Embedding Strategy

Embedding unit: `EvidenceChunk`. Provider: `mdarix-deterministic`. Model: `mdarix-hash-bow-32`.

## 6. Embedding Model / Dimension

Model version: `1.0`. Dimension: `32`. Pipeline version: `R1-Day9`.

## 7. PGVECTOR Implementation

Implemented `evidence_chunk_embeddings.embedding vector(32)` with HNSW cosine index.

## 8. Embedding Provenance

Stored tenant, evidence, chunk, checksum, provider, model, model version, dimension, pipeline version, distance metric, status, and failure reason.

## 9. Indexing

`TrustedRetrievalService.index_evidence_chunks` indexes trusted chunks idempotently and records controlled failures.

## 10. Structured Retrieval

Uses canonical metadata and `EvidenceEntityLink` lifecycle context.

## 11. Semantic Retrieval

Uses pgvector cosine search over indexed chunk embeddings.

## 12. Hybrid Retrieval

Merges structured and semantic candidates, deduplicates by chunk, and records deterministic reasons.

## 13. Ranking

Ranking is retrieval relevance only. It is not truth, confidence, evidence strength, regulatory significance, or root-cause probability.

## 14. Deduplication

Same chunk returned by multiple mechanisms appears once as a hybrid result.

## 15. Lifecycle Context

Lifecycle filters are enforced before result presentation.

## 16. Product Context

Controlled tests prevent wrong-Product evidence from being presented as applicable.

## 17. ProductVersion Context

Rev D-scoped retrieval preserves ProductVersion distinction.

## 18. Shared Component Handling

Component context is not treated as sufficient to override Product/ProductVersion filters.

## 19. Lot Context

Lot filters are supported when lot context is available.

## 20. Investigation Context

Investigation filters are supported through evidence investigation metadata and linked investigation evidence.

## 21. Temporal Retrieval

Supports `current`, `event`, and `known` modes.

## 22. Event-As-Of

`event` mode uses effective/event semantics.

## 23. Known-As-Of

`known` mode uses ingestion/availability semantics.

## 24. Future-Leakage Test

PASS. Future evidence leakage in KNOWN-AS-OF: `0`.

## 25. Source Anchors

PASS. Material retrieved result source-anchor coverage: `100%`.

## 26. Retrieval Provenance

Implemented `retrieval_queries` with query text, filters, mode, temporal mode, embedding model, config version, top K, returned refs, status, and timestamp.

## 27. Insufficient-Evidence Behavior

Implemented `NO_RELEVANT_EVIDENCE` and `INSUFFICIENT_RELEVANT_EVIDENCE` statuses.

## 28. Confirmation-Bias Test

PASS. Leading causal wording does not create causal output.

## 29. Contradictory-Evidence Retrieval

Retrieval preserves contextual and contradictory evidence candidates where indexed and context-valid. No causal conclusion is generated.

## 30. Duplicate Handling

PASS. Structured/vector duplicate chunks are collapsed.

## 31. Wrong-Product Test

PASS. Wrong Product presented as applicable: `0`.

## 32. Wrong-Version Test

PASS. Wrong Version presented as applicable: `0`.

## 33. VS001 Walkthrough

VS001 query coverage includes shutdown complaints, Rev D/Product context, Component context, validation evidence, late-evidence exclusion in known-as-of, and no causal conclusion.

## 34. VS002-VS012 Results

Day 9 scope validates retrieval guardrails relevant to false correlation, missing evidence, conflicting evidence, incorrect timeline, shared component, premature closure, control evidence, model provenance, multiple causes, and abstention/no-match. Formal per-scenario retrieval labels remain a future evaluation enhancement.

## 35. Retrieval Metrics

Automated Day 9 tests: `14 passed`. Validator: PASS. Full regression: `155 passed`. Retrieval provenance rows observed by validator: `28`.

Formal broad Precision@K/Recall@K/MRR are not claimed because no standalone Day 9 relevance-label file exists outside Ground Truth.

## 36. Negative Retrieval Results

No-match behavior returns `NO_RELEVANT_EVIDENCE` without forcing unrelated evidence.

## 37. Tenant Isolation

PASS. Cross-tenant retrieval leakage: `0` in controlled tests.

## 38. Ground Truth Isolation

PASS. Ground Truth indexed: `0`. Ground Truth retrieved: `0`.

## 39. Prompt-Injection Content Test

PASS. Prompt-injection text is treated as retrieval input data and does not alter policy or create causal claims.

## 40. Automated Test Results

`python -m pytest tests\test_day9_retrieval.py -q --basetemp .pytest_tmp`

Result: `14 passed`.

## 41. Validator Result

`python infrastructure\database\scripts\day9_validate_retrieval.py`

Result: PASS.

## 42. Regression Result

`python -m pytest tests -q --basetemp .pytest_tmp`

Result: `155 passed`.

Day 8 validator after Day 9: PASS.

## 43. Performance Sanity

Controlled local dataset retrieval and indexing complete within pytest/validator runtime. No enterprise-scale performance claim is made.

## 44. Security Review

PASS for Day 9 scope: tenant filter, safe top K, source anchors, no arbitrary SQL API, no Ground Truth indexing, no Ground Truth retrieval, no causal output, and explicit retrieval provenance.

## 45. Database Migration

Created Alembic revision `b19d4c6a2f91`.

## 46. Files Created/Modified

- `backend/app/db/models/retrieval_intelligence.py`
- `backend/app/retrieval/`
- `retrieval/`
- `infrastructure/database/migrations/versions/b19d4c6a2f91_create_day9_trusted_retrieval.py`
- `infrastructure/database/scripts/day9_validate_retrieval.py`
- `tests/test_day9_retrieval.py`
- Retrieval docs, diagrams, evaluation report, and Day 10 contract

## 47. Open Decisions

Formal Day 9 relevance-label files should be added before claiming broad Precision@K, Recall@K, or MRR across all VS001-VS012.

## 48. Validation Matrix

| Gate | Status |
| --- | --- |
| Day 8 prerequisite | PASS |
| pgvector | PASS |
| embedding provider | PASS |
| embedding model | PASS |
| embedding dimension | PASS |
| embedding persistence | PASS |
| embedding provenance | PASS |
| embedding idempotency | PASS |
| embedding regeneration | PASS |
| embedding failure | PASS |
| structured retrieval | PASS |
| semantic retrieval | PASS |
| hybrid retrieval | PASS |
| ranking | PASS |
| deduplication | PASS |
| Product context | PASS |
| ProductVersion context | PASS |
| Component context | PASS |
| Supplier context | PASS |
| Lot context | PASS |
| Complaint context | PASS |
| Investigation context | PASS |
| event-as-of | PASS |
| known-as-of | PASS |
| future leakage | PASS |
| source anchors | PASS |
| retrieval provenance | PASS |
| empty query | PASS |
| long query | PASS |
| no match | PASS |
| insufficient evidence | PASS |
| top-K bounds | PASS |
| confirmation-bias query | PASS |
| wrong Product | PASS |
| wrong Version | PASS |
| tenant isolation | PASS |
| Ground Truth isolation | PASS |
| prompt-injection content | PASS |
| VS001 | PASS |
| VS002-VS012 retrieval guardrails | PASS |
| automated tests | PASS |
| validator | PASS |
| retrieval evaluation | PASS |
| regression | PASS |
| documentation | PASS |
| Day-10 contract | PASS |
| Git status | LOCAL COMMIT PASS / REMOTE PUSH PENDING |

## 49. Git Status

Committed locally with message `feat: establish MDARIX R1 trusted evidence retrieval with pgvector`. Remote push to `origin/main` is pending explicit approval because the approval reviewer blocked a large direct push to `main`.

## 50. Day 10 Readiness

Ready for Day 10 after remote push approval/completion.
