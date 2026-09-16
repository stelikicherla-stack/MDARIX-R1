# MDARIX R1 Day 9 Retrieval Handoff Contract

## 1. Day 8 Deliverables Handoff to Day 9

Day 8 provides trustworthy, grounded evidence structures:
- Canonical `Evidence` records and preserved source content
- Semantic `EvidenceChunk` records with locators and sequence ordering
- `EvidenceObservation` records with 100% source anchor locators
- `EvidenceEntityLink` records linked to canonical lifecycle objects (`Product`, `Component`, `Supplier`, `Lot`, etc.)
- `AIExecution` provenance records
- Tenant isolation and Ground Truth evaluation sets

## 2. Day 9 Responsibilities

Day 9 will build upon Day 8 foundation by adding:
- `pgvector` vector embedding generation for `EvidenceChunk`
- Index creation (`ivfflat` or `hnsw` pgvector index)
- Hybrid semantic + structured filtering search API
- Retrieval evaluation metrics (Recall, Precision@K, Grounding relevance)
