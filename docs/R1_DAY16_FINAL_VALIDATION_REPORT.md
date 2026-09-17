# MDARIX R1 Day 16 Final Technical Closure

## Validation scope

This validation used the live local application and canonical PostgreSQL environment. No Ground Truth content was supplied to runtime reasoning.

## VS009 live discovery

The golden scenario index identifies VS009 as `INV-009`, titled Counterfactual. Live data currently identifies `INV-009` as a NimbusView 200 Monitor investigation about AI model-change comparison. The Rev-B shutdown data is associated with AsterFlow `INV-001`. This is a golden-index/live-data alignment defect, not a reason to relabel runtime data.

### Lineage classification

| Artifact | Product | ProductVersion | Investigation | Intervention target | Source / status |
|---|---|---|---|---|---|
| `evaluation/ground_truth/VS009/ground_truth.json` | not specified | not specified | INV-009 | not specified | Evaluation-only Ground Truth; authoritative scenario key |
| `evaluation/scenarios/scenario_index.json` | not specified | not specified | INV-009 | not specified | Derived index; consistent with Ground Truth |
| `data/golden/generators/generate_r1_golden_dataset.py` | Nimbus mapping by ID | not specified | INV-009 | not specified | Synthetic generator; generic sequential mapping |
| `data/golden/source/qms/investigations.csv` | NimbusView 200 Monitor | not specified | INV-009 | AI model-change comparison | Live seed source; inconsistent with counterfactual evidence |
| `data/golden/source/evidence/EV-VS001-*` | AsterFlow 100 Controller | Rev D | INV-001 | Component Rev B | Counterfactual-relevant evidence; valid Rev-B evidence lineage |

Classification: `INCORRECT_LIVE_SEED_DATA` / `MULTIPLE_DEFECTS` in the scenario-to-fixture mapping. Ground Truth was not changed because it is evaluation-only and consistently identifies INV-009. No safe correction can repurpose INV-009 without damaging the separate live AI-model scenario. The correct remediation requires an approved fixture/data-lineage decision: either seed the intended counterfactual records under the canonical INV-009 product/version or revise the scenario mapping through an approved dataset change while preserving Ground Truth semantics.

The approved minimal fixture at `evaluation/fixtures/VS009_counterfactual_fixture.json` now uses the existing Nimbus narrative: NimbusView Rev B, INV-009, intervention `REMOVE_CHANGE`, target `CHG-GEN-006`. It does not copy the AsterFlow/Component Rev B narrative. Live execution returned `SUCCESS`, persisted a derived Scenario and AIExecution, retained limitations, and stated that the intervention weakens the explanation without establishing causality. VS009 canonical identity and live integration are now PASS.

| Entity | Live value |
|---|---|
| Tenant | ACME_CARE_SYNTHETIC (`414e8075-26e8-456e-b2b2-330919f02eed`) |
| Rev-B investigation | INV-001 (`5a541092-f384-44eb-a832-3137749e7393`) |
| Rev-B product | AsterFlow 100 Controller (`5422edef-6536-4283-b715-b0d4fba3ca0a`) |
| Rev-B ProductVersion | Rev D (`94f9eeaa-11d2-46c0-a12a-0643746b5dd4`) |
| Golden-index VS009 investigation | INV-009 (`55c26a9e-654d-486c-88b2-c60998e570d8`) |
| Golden-index VS009 product | NimbusView 200 Monitor (`306e4828-000c-49a2-9342-461a7c3412a6`) |

The real API path was exercised for the Rev-B investigation. It returned `SUCCESS`, persisted a derived Scenario, recorded an AIExecution, preserved observed evidence and limitations, weakened candidate links, and made no root-cause or causal claim. The runtime result was labelled `COUNTERFACTUAL / WHAT-IF — NOT OBSERVED EVIDENCE`.

## ProductVersion and temporal validation

The live workspace selected Rev D for INV-001. The service now accepts an explicit `product_version_id` and rejects a ProductVersion belonging to another product. A live request with Nimbus INV-009 and Nimbus Rev B succeeded; a mismatched AsterFlow Rev D ProductVersion was rejected. Current/Event/Known temporal validation remains enforced by the existing workspace path.

The remaining limitation is that the existing Product 360 change/evidence aggregation contains shared product-level records; a complete record-by-record cross-version matrix requires the broader existing data model to expose applicability consistently for every entity. No contamination was silently reclassified as safe.

## Warnings

The full regression reproduced exactly two warnings:

1. `StarletteDeprecationWarning` at `site-packages/fastapi/testclient.py:1`: Starlette imports the deprecated `httpx` compatibility path. Triggered by the third-party FastAPI/Starlette TestClient stack. Classification: THIRD_PARTY_DEPRECATION. Non-functional; do not patch installed packages. Future action: upgrade compatible FastAPI/Starlette/httpx versions together.
2. `DeprecationWarning` at `site-packages/starlette/testclient.py:53`: Starlette uses the deprecated `anyio.abc.BlockingPortal` alias. Triggered by the same third-party TestClient stack. Classification: THIRD_PARTY_DEPRECATION. Non-functional; future action is dependency maintenance.

Warnings are understood; none are unexplained, application defects, security defects, or data-integrity defects.

## Automated results

- Targeted Day 16 tests: 11 passed, 0 failed, 0 errors.
- Full regression: 199 passed, 0 failed, 0 errors, 2 third-party warnings.
- Frontend build: passed.
- Manual Counterfactual UI: previously human-confirmed PASS; no Counterfactual UI semantics were changed.

## Status

Day 16 remains blocked only because a complete live cross-version positive/negative applicability matrix cannot be asserted from the current applicability data. No Ground Truth or runtime canonical record was rewritten to force a pass.

## Live applicability matrix evidence

For NimbusView, Product 360 returned the following live counts at the controlled cutoff `2026-02-15`:

| Cell | Components | Lots | Complaints | Evidence | Changes |
|---|---:|---:|---:|---:|---:|
| Rev A / Current | 2 | 0 | 9 | 10 | 16 |
| Rev A / Event-as-of | 2 | 0 | 9 | 0 | 12 |
| Rev A / Known-as-of | 2 | 0 | 9 | 0 | 12 |
| Rev B / Current | 3 | 4 | 21 | 10 | 16 |
| Rev B / Event-as-of | 3 | 4 | 14 | 0 | 12 |
| Rev B / Known-as-of | 3 | 4 | 3 | 0 | 12 |

The live counts prove meaningful temporal differences, including Event versus Known complaint eligibility, but the current Product 360 aggregation does not expose stable version-applicability labels for every change/evidence/graph record. Therefore positive and negative record-level assertions for all six cells remain blocked rather than inferred from aggregate counts.

Seed-function determinism was checked by building the existing deterministic golden dataset twice: both builds produced identical SHA-256 content hashes. The fixture is stored outside the generator-reset directory so golden validation cannot delete it. Database seed execution itself is not implemented by this repository’s generator; no duplicate-producing seed command was available to run.

## Final remediation test results

- VS009 fixture and counterfactual tests: 11 passed, 0 failed.
- Full regression after fixture repair: 199 passed, 0 failed, 0 errors, 2 understood third-party warnings.
