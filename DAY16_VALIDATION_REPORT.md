# MDARIX R1 — DAY 16 VALIDATION REPORT

## Constrained Counterfactual Intelligence

Day 16 completed the constrained counterfactual workflow and ProductVersion × temporal applicability validation.

### Scope completed

- Canonical VS009: NimbusView 200 Monitor, Rev B, INV-009.
- Controlled intervention: `REMOVE_CHANGE` targeting `CHG-GEN-006`.
- Counterfactual result is explicitly derived, hypothetical, and not observed evidence.
- Human authority, evidence grounding, provenance, tenant isolation, and Ground Truth isolation preserved.
- AsterFlow Rev-B counterfactual regression preserved.
- ProductVersion × temporal applicability fixture added for NimbusView Rev A and Rev B.
- Positive and negative assertions added for Current, Event-as-of, and Known-as-of contexts.
- Exact Event-vs-Known case validated with `NV-LATE-KNOWN`.
- Foreign-tenant, shared-product, future, change, evidence, and graph controls included.

### Validation results

| Gate | Result |
|---|---|
| VS009 live integration | PASS |
| VS009 semantics | PASS |
| ProductVersion isolation | PASS |
| Temporal isolation | PASS |
| Cross-version contamination | 0 |
| Future leakage | 0 |
| Ground Truth leakage | 0 |
| Canonical mutations | 0 |
| Fixture idempotency | PASS |
| Targeted tests | 20 passed |
| Full regression | 208 passed, 0 failed, 0 errors |
| Frontend build | PASS |
| Unexplained warnings | 0 |
| Critical defects | 0 |

Two understood third-party deprecation warnings remain documented for dependency maintenance.

Detailed evidence is available in [R1_DAY16_FINAL_VALIDATION_REPORT.md](docs/R1_DAY16_FINAL_VALIDATION_REPORT.md).

## Git

- Commit: `6565715ec5ecdf81ee2c8650c75d69f5c692d906`
- Status: pushed to `origin/main`
