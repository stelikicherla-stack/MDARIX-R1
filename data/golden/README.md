# MDARIX R1 Golden Dataset

MDARIX R1 GOLDEN DATASET - SYNTHETIC TEST DATA ONLY. NOT FOR CLINICAL OR REGULATORY USE.

## Purpose

This dataset is an evaluation asset for MDARIX R1. It is designed to test whether MDARIX can reconstruct product reality, relate evidence, challenge premature causal claims, identify unknowns, and support human decision review.

## Dataset Version

`r1-day3-golden-v1`

The dataset is generated deterministically with seed `31003`.

## Fictional Company

The primary fictional manufacturer is `AcmeCare Instruments`. It does not represent a real company, customer, patient population, or medical-device incident set.

## Architecture

The dataset has three separated layers:

- Source data: fragmented synthetic source-system files under `data/golden/source/`.
- Canonical data: normalized application-facing JSON under `data/golden/canonical/`.
- Ground Truth: evaluation-only files under `evaluation/ground_truth/`.

Ground Truth must not flow into normal application retrieval.

## Directory Structure

- `GOLDEN_DATASET_MANIFEST.json`: version, counts, hash, and layer paths.
- `source/`: QMS-like, PLM-like, ERP/MES-like, and evidence source files.
- `canonical/`: normalized Golden Dataset aligned to the Day 2 schema.
- `generators/`: deterministic generator.
- `validate_golden_dataset.py`: reusable validation command.
- `evaluation/ground_truth/`: hidden evaluation-only truth by scenario.

## Generation

```powershell
.\.venv\Scripts\python.exe data\golden\generators\generate_r1_golden_dataset.py
```

## Validation

```powershell
.\.venv\Scripts\python.exe data\golden\validate_golden_dataset.py
.\.venv\Scripts\python.exe -m pytest tests\test_day3_golden_dataset.py -q
```

## Known Intentional Anomalies

- Product version identity variations.
- Supplier aliases.
- Missing lot/component traceability.
- Delayed record entry.
- Duplicate complaint candidates.
- Late-arriving evidence.
- False temporal correlation.
- Multiple plausible complaint mechanisms.

## Relationship to Golden Scenarios

The dataset implements VS001 through VS012. Application-facing records support the scenarios, while expected conclusions, prohibited conclusions, hidden causal structure, and abstention behavior are stored only in `evaluation/ground_truth/`.

## Safe Reset

Regenerate files using the generator. Do not drop the database, schema, Docker volume, pgvector extension, or Alembic history.
