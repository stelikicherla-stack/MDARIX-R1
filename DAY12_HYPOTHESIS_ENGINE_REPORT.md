# MDARIX R1 Day 12 Competing Hypothesis Engine Report

## 1. Entry Gate

Local Day 11 product baseline: PASS.

GitHub synchronization is user-managed and not used as a Day 12 gate.

## 2. Architecture

Implemented a controlled Competing Hypothesis Engine over Day 11 `InvestigationAnalysis`.

## 3. Contract

Implemented `HypothesisSet`, `Hypothesis`, and explicit hypothesis/evidence relationships.

## 4. Evidence Semantics

Relationships distinguish `SUPPORTS`, `CONTRADICTS`, `CONTEXTUAL`, `INSUFFICIENT`, and `UNRESOLVED`.

## 5. Guardrails

- Hypothesis is not fact
- Hypothesis is not root cause
- Support is not proof
- No forced numeric probability
- Human authority required

## 6. API

- `POST /api/v1/investigations/{id}/hypotheses`
- `GET /api/v1/investigations/{id}/hypotheses`
- `GET /api/v1/investigations/{id}/hypotheses/{hypothesis_id}`

## 7. UI

Added a Competing Hypotheses section to the Investigation Workspace.

## 8. Validation

Day 12 tests:

`python -m pytest tests\test_day12_hypothesis_engine.py -q --basetemp .pytest_tmp`

Result: `9 passed`.

Day 12 validator:

`python infrastructure\database\scripts\day12_validate_hypothesis_engine.py`

Result: PASS.

Full regression:

`python -m pytest tests -q --basetemp .pytest_tmp`

Result: `177 passed`.

Frontend build:

`npm.cmd run build`

Result: PASS.

## 9. Evaluation Metrics

- Hypothesis evidence grounding: `9/9`
- Source-anchor validity: `6/6`
- Unsupported material evidence relationships: `0`
- Invented evidence: `0`
- Unsupported causal conclusions: `0`
- Forced numeric probabilities: `0`
- Contradiction preservation: `3/3`
- Alternative hypothesis preservation: `3/2`
- Future-information leakage: `0`
- Ground Truth leakage: `0`
- Tenant leakage: `0`
- Wrong-version contamination: `0`
- Prompt-injection policy violations: `0`
- Historical root cause converted to fact: `0`
- Provenance completeness: `1/1`

## 10. Day 13 Readiness

Day 13 can consume validated `HypothesisSet` without rebuilding from raw database data.

## 11. Final Decision

DAY 12 PASSED - MDARIX R1 COMPETING HYPOTHESIS ENGINE READY.

READY FOR DAY 13 - AI CHALLENGER.

## 12. GitHub Status

USER-MANAGED - NOT USED AS A DAY 12 PASS/FAIL GATE.
