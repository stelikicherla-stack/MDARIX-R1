# MDARIX R1 Day 3 Golden Data Foundation Report

## 1. Day 3 Status

PASS.

Day 3 created a deterministic, synthetic, evidence-rich Golden Dataset foundation. It did not implement Day 4 ingestion, Day 5 identity resolution logic, Day 6 Reality Graph APIs, AI investigators, UI, connectors, or production workflows.

## 2. Entry Gate Results

Day 0: PASS.

Day 1: PASS.

Day 2: PASS.

Runtime gates passed: Docker, PostgreSQL 16.15, pgvector 0.8.6, Alembic head `ea1eb54290f5`, Python 3.13 venv, Day 2 validator, and Day 2 automated tests.

## 3. Dataset Version

`r1-day3-golden-v1`

Deterministic seed: `31003`

Synthetic-only notice:

```text
MDARIX R1 GOLDEN DATASET - SYNTHETIC TEST DATA ONLY. NOT FOR CLINICAL OR REGULATORY USE.
```

## 4. Fictional Company / Product Summary

Fictional company: `AcmeCare Instruments`.

Product families:

- `AsterFlow Infusion Platform`
- `NimbusView Monitoring Platform`

Primary scenario product: `AsterFlow 100 Controller`, especially `Rev D`.

## 5. Actual Record Counts

| Record Type | Count |
| --- | ---: |
| Product families | 2 |
| Products | 2 |
| Product versions | 6 |
| Components | 16 |
| Suppliers | 5 |
| Manufacturing sites | 2 |
| Lots | 18 |
| Requirements | 24 |
| Changes | 16 |
| Complaints | 120 |
| Investigations | 10 |
| Risks | 15 |
| Failure modes | 15 |
| Controls | 12 |
| Evidence artifacts | 38 |
| Hypotheses | 3 |
| Unknowns | 3 |
| Failure chains | 1 |
| Scenarios | 12 |
| Intentional anomalies | 8 |

## 6. Source Data Summary

Source files are stored under `data/golden/source/`:

- PLM-like product, version, component, requirement, and change CSV files.
- QMS-like complaints, investigations, risks, failure modes, and controls CSV files.
- ERP/MES-like suppliers, sites, and lots CSV files.
- Evidence Markdown files and JSON metadata.

## 7. Canonical Data Summary

Canonical application-facing data is stored at:

```text
data/golden/canonical/r1_canonical_golden_dataset.json
```

It contains normalized product, lifecycle, complaint, investigation, evidence, hypothesis, unknown, failure-chain, anomaly, and scenario records aligned to the Day 2 schema concepts.

## 8. Ground Truth Architecture

Ground Truth is isolated under:

```text
evaluation/ground_truth/
```

Ground Truth includes hidden causal structures, prohibited conclusions, expected unknowns, contradictions, and acceptance behavior. Application-facing canonical data does not contain `hidden_ground_truth`, `correct_answer`, `actual_root_cause`, `expected_conclusion`, or `prohibited_conclusions`.

## 9. Primary VS001 Scenario

VS001 represents:

Supplier process change -> Component Rev B -> Product Rev D configuration -> affected lots -> increased shutdown complaints.

The dataset supports this as a leading hypothesis while preserving uncertainty.

## 10. Contradictions

VS001 includes:

- At least three shutdown complaints before Component Rev B.
- A relevant Rev B qualification/validation test passed.
- Incomplete lot/component traceability.
- Comparative Rev A vs Rev B testing unavailable.

## 11. Unknowns

Explicit unknowns include:

- Comparative Rev A vs Rev B testing unavailable.
- Incomplete component genealogy for LOT-010 and LOT-013.
- Missing field operating conditions for the abstention scenario.

## 12. False Correlations

VS002 includes packaging label revision `CHG-LABEL-042`, which occurs near the complaint increase but has no causal electrical mechanism.

## 13. Temporal Complexity

The dataset distinguishes event, effective, recorded, and ingestion timestamps. It includes delayed QMS entry and late-arriving lot genealogy evidence.

## 14. Identity Variations

Controlled identity variations include:

- `PRD-100-D`
- `PRD100 Rev D`
- `Product-100 / Revision D`

Supplier aliases include `Nova Cap` and `NVC Components`.

## 15. Late-Arriving Information

Lot genealogy evidence `EV-VS001-003` arrives after a plausible initial closure point, enabling later evaluation of what was known at decision time versus what became known later.

## 16. Shared Component Exposure

Shared component exposure is represented through reusable component records and lot/component traceability, especially the Power Regulation Module.

## 17. Premature Closure Case

VS007 includes a plausible historical closure weakness where pre-Rev B complaints and unresolved unknowns were not adequately addressed.

## 18. Control Failure Case

VS008 includes process-control and validation-related evidence artifacts that can support or weaken future control-failure analysis.

## 19. Multiple-Cause Case

VS011 includes shutdown subsets consistent with more than one plausible mechanism, preventing a forced single-root-cause narrative.

## 20. Correct-Abstention Case

VS012 contains insufficient field operating condition evidence. Correct future behavior is to abstain or request more evidence.

## 21. All 12 Golden Scenarios

VS001 through VS012 are represented in the canonical scenario index and have evaluation-only Ground Truth files.

## 22. Determinism Results

PASS.

The generator was rerun during tests and reproduced the same canonical SHA-256 hash.

## 23. Ground Truth Leakage Test

PASS.

Automated tests and the validator confirm application-facing canonical data does not contain evaluation-only Ground Truth answer keys.

## 24. Automated Test Results

Day 2 + Day 3 test suite:

```text
28 passed
```

Day 3-specific tests:

```text
11 passed
```

Golden Dataset validator:

```text
GOLDEN DATASET VALIDATION = PASS
```

## 25. Data Quality Results

Intentional anomalies are documented and controlled: identity variations, supplier aliases, missing traceability, delayed entry, duplicate candidates, late-arriving evidence, false correlation, and multiple causes.

## 26. Security / PII Check

PASS.

The dataset is fictional, synthetic, non-personal, non-customer, and non-production. No secrets, tokens, database dumps, real patient data, or real customer data are included.

## 27. Files Created/Modified

- `data/golden/README.md`
- `data/golden/GOLDEN_DATASET_MANIFEST.json`
- `data/golden/source/`
- `data/golden/canonical/r1_canonical_golden_dataset.json`
- `data/golden/generators/generate_r1_golden_dataset.py`
- `data/golden/validate_golden_dataset.py`
- `evaluation/ground_truth/`
- `evaluation/scenarios/scenario_index.json`
- `docs/R1_GOLDEN_SCENARIOS.md`
- `docs/R1_GOLDEN_DATA_DICTIONARY.md`
- `docs/diagrams/R1_GOLDEN_DATA_LINEAGE.md`
- `tests/test_day3_golden_dataset.py`
- `DAY3_GOLDEN_DATA_FOUNDATION_REPORT.md`

## 28. Open Decisions

No blocking open dataset decisions.

Non-blocking future decisions:

- How Day 4 ingestion maps each source file into Day 2 tables.
- Which dataset subset should be loaded first into PostgreSQL for Day 4 validation.
- How strict future identity-resolution scoring should be for aliases.

## 29. Validation Matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| Day 0 prerequisite | PASS | Reports and live checks |
| Day 1 prerequisite | PASS | Report and specs |
| Day 2 prerequisite | PASS | Tests and validator |
| Golden Dataset version | PASS | `r1-day3-golden-v1` |
| Synthetic-only declaration | PASS | Notice in manifest/docs/data |
| Fictional company | PASS | AcmeCare Instruments |
| 2 product families | PASS | Count = 2 |
| 4+ product versions | PASS | Count = 6 |
| 15-20 components target | PASS | Count = 16 |
| 5 suppliers target | PASS | Count = 5 |
| 2 manufacturing sites | PASS | Count = 2 |
| 15-20 lots target | PASS | Count = 18 |
| 15-20 changes target | PASS | Count = 16 |
| 100-150 complaints target | PASS | Count = 120 |
| 10 investigations target | PASS | Count = 10 |
| Risks | PASS | Count = 15 |
| Failure modes | PASS | Count = 15 |
| Controls | PASS | Count = 12 |
| 30-50 evidence artifacts target | PASS | Count = 38 |
| Source data layer | PASS | `data/golden/source` |
| Canonical data layer | PASS | `data/golden/canonical` |
| Ground Truth layer | PASS | `evaluation/ground_truth` |
| Ground Truth isolation | PASS | Leakage test |
| Deterministic generation | PASS | Repeatability test |
| Dataset manifest | PASS | Manifest JSON |
| Temporal integrity | PASS | Tests |
| Identity variations | PASS | Alias map |
| Late-arriving evidence | PASS | EV-VS001-003 |
| Supporting evidence | PASS | VS001 evidence |
| Contradicting evidence | PASS | VS001 evidence |
| Explicit unknowns | PASS | Unknown records |
| False correlations | PASS | VS002 |
| Shared components | PASS | VS006 |
| Premature closure | PASS | VS007 |
| Control-failure scenario | PASS | VS008 |
| Multiple-cause scenario | PASS | VS011 |
| Correct-abstention scenario | PASS | VS012 |
| VS001 | PASS | Ground Truth + canonical data |
| VS002 | PASS | Ground Truth + canonical data |
| VS003 | PASS | Ground Truth + canonical data |
| VS004 | PASS | Ground Truth + canonical data |
| VS005 | PASS | Ground Truth + canonical data |
| VS006 | PASS | Ground Truth + canonical data |
| VS007 | PASS | Ground Truth + canonical data |
| VS008 | PASS | Ground Truth + canonical data |
| VS009 | PASS | Ground Truth + canonical data |
| VS010 | PASS | Ground Truth + canonical data |
| VS011 | PASS | Ground Truth + canonical data |
| VS012 | PASS | Ground Truth + canonical data |
| Automated dataset tests | PASS | 11 Day 3 tests passed |
| Ground Truth leakage test | PASS | Tests and validator |
| Validation script | PASS | Validator passed |
| Golden Dataset README | PASS | Created |
| Data dictionary | PASS | Created |
| Lineage diagram | PASS | Created |
| Secret scan | PASS | No secrets found |
| PII check | PASS | No PII markers found |
| Git status | PASS | Day 3 commits pushed to `origin/main` |

## 30. Git Commit/Push Status

PASS.

Day 3 Golden Dataset foundation commit:

```text
ed1d5a8 feat: establish MDARIX R1 golden dataset foundation
```

The commit was pushed to `origin/main`.

## 31. Day 4 Readiness

Ready for Day 4 after Day 3 artifacts are committed and pushed. Day 4 scope is Multi-Source Ingestion.
