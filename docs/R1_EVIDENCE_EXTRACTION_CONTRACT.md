# MDARIX R1 Evidence Extraction Contract

## 1. Overview

This contract defines the interface, schema inputs/outputs, validation rules, idempotency requirements, and error handling for the MDARIX Evidence Extraction Pipeline.

## 2. Input / Output Contracts

### Inputs
- `evidence_id`: UUID of canonical evidence record
- `tenant_id`: UUID of tenant
- `reprocess`: Boolean flag indicating whether to force reprocessing

### Outputs (`EvidenceExtractionResult`)
- `evidence_id`: String UUID
- `observations`: List of `ExtractedObservationSchema`
  - `statement`:Verbatim or structured claim statement
  - `observation_type`: `EXPLICIT_SOURCE_STATEMENT`, `STRUCTURED_EXTRACTION`, `DETERMINISTIC_DERIVATION`, `AI_EXTRACTED_OBSERVATION`
  - `source_anchor`: `paragraph_index`, `excerpt`, `character_range`
- `entity_candidates`: Candidate entity links
- `limitations`: Noted evidence limitations
- `extraction_status`: `COMPLETED`, `COMPLETED_WITH_LIMITATIONS`, `EXTRACTION_FAILED`

## 3. Idempotency & Reprocessing

- Repeat extraction runs against unchanged evidence produce identical chunks and observation IDs.
- Reprocessing deletes previous chunks and updates observation records without losing historical `AIExecution` log entries.
