# MDARIX R1 Day 5 Normalization Contract

## Purpose

Day 5 receives staged source records from Day 4 and performs normalization plus identity resolution. Day 4 does not perform those responsibilities.

## Day 5 Inputs

Each staged record provides:

- Tenant
- Ingestion run
- Source system
- Source type
- Record type
- Source file
- Source row/index
- Source record ID
- Raw payload
- Parsed payload
- Candidate canonical payload
- Source checksum
- Source/effective/recorded timestamps where available
- Ingestion timestamp
- Data quality status
- Mapping version
- Quality issues

## Day 5 Responsibilities

- Normalize source values.
- Resolve identity aliases.
- Map source records to canonical Day 2 tables.
- Resolve lifecycle relationships.
- Preserve source provenance.
- Promote quality issues where needed.

## Explicit Non-Inputs

Day 5 must not consume `evaluation/ground_truth/` as application data. Ground Truth remains evaluation-only.

## Examples

`PRD-100-D`, `PRD100 Rev D`, and `Product-100 / Revision D` are preserved by Day 4. Day 5 determines whether and how they map to a canonical `ProductVersion`.

`Nova Cap` and `NVC Components` are preserved as source supplier strings. Day 5 resolves aliases only with controlled identity logic.
