# MDARIX R1 Ingestion Architecture

## Purpose

Day 4 establishes a controlled ingestion foundation for synthetic QMS, PLM, ERP/MES, and evidence sources. It preserves source fidelity, timestamps, checksums, quality issues, provenance, and lineage for later normalization.

## Boundary

Day 4 does not perform identity resolution, canonical merge, graph construction, AI analysis, complaint classification, or root-cause reasoning.

## Pipeline

DISCOVER SOURCE -> REGISTER INGESTION RUN -> READ SOURCE -> VALIDATE FILE -> PRESERVE RAW SOURCE -> PARSE STRUCTURE -> VALIDATE RECORD -> STAGE RECORD -> CAPTURE QUALITY ISSUES -> CAPTURE PROVENANCE -> PRODUCE RESULT -> HAND OFF FOR DAY 5 NORMALIZATION.

## Source Adapters

- `CSVSourceAdapter`: CSV source files.
- `JSONSourceAdapter`: JSON source metadata.
- `EvidenceFileAdapter`: Markdown/text evidence artifacts.

Adapters read and validate source structure only. They do not normalize identity values.

## Ingestion Run

`ingestion_runs` records source system, type, file path, checksum, timestamps, status, counts, mapping version, configuration version, initiator, and provenance.

Statuses:

- `RUNNING`
- `COMPLETED`
- `COMPLETED_WITH_WARNINGS`
- `FAILED`
- `ALREADY_INGESTED`

## Source Records

`staged_source_records` preserves raw payload, parsed payload, candidate canonical payload, source identifiers, source row/index, source timestamps, ingestion timestamp, checksum, mapping version, and data quality status.

## Raw Preservation

Raw source values are retained in JSONB. Source strings such as `PRD100 Rev D` and supplier aliases are not silently changed.

## Checksums

Files use SHA-256 checksums. Record payloads use deterministic SHA-256 over sorted JSON.

## Mappings

Mappings live under `ingestion/mappings/` as versioned JSON contracts. They define source system, record type, schema version, mapping version, required fields, field mappings, and timestamp semantics.

## Quality Issues

`data_quality_issues` stores controlled issue codes with severity `INFO`, `WARNING`, or `ERROR`. Warnings preserve valid but imperfect source records, such as missing lot references or incomplete traceability.

## Error Handling

Malformed files produce `FAILED` ingestion runs with safe error summaries. Valid files with imperfect records complete with warnings.

## Transaction Strategy

R1 uses one transaction per source file. File-level schema failure marks that file run failed. Valid Golden Dataset files stage records atomically per file.

## Idempotency

If the same source system, file path, and checksum have already completed, Day 4 records a new `ALREADY_INGESTED` run and does not duplicate staged source records.

## Ground Truth Isolation

Ingestion rejects paths under `evaluation/ground_truth/`. Application-facing ingestion reads only `data/golden/source/`.

## Security

The ingestion layer uses controlled local paths, rejects unsupported formats, stores safe errors, and does not execute source content. `.env`, backups, and secrets remain excluded from Git.

## Observability

Ingestion can report files discovered, files ingested, records seen, accepted records, warning records, rejected records, duplicate source records, quality issues, checksums, source paths, and run statuses.

## Day 5 Handoff

Day 5 receives staged source records with raw values, parsed values, source timestamps, mapping version, quality status, source provenance, and candidate canonical payloads.
