# MDARIX R1 Day 16 Counterfactual Validation Report

## Scope and architecture

Day 16 adds constrained counterfactual reasoning using the existing tenant-scoped `Scenario` entity for separate derived records and the existing `AIExecution` governance record for execution provenance. Canonical Product, ProductVersion, Investigation, Evidence, graph, complaint, change, and failure-chain inputs are read only.

Supported intervention types are `REMOVE_CHANGE`, `REPLACE_COMPONENT_REVISION`, `REMOVE_SUPPLIER_CHANGE`, `REMOVE_FAILURE_CHAIN_LINK`, `REMOVE_HYPOTHESIZED_RELATIONSHIP`, `COMPARE_HYPOTHESES`, and `TEST_TEMPORAL_DEPENDENCY`.

## Reasoning controls

The service constructs a baseline through the existing Investigation Workspace, preserving the selected temporal mode and as-of date. It validates tenant/investigation ownership, temporal requirements, supported intervention type, and readable target existence before producing a derived comparison. Results are explicitly marked derived, hypothetical, and non-observed. Graph adjacency is reported as potentially affected relationships and never promoted to causality.

Invariants preserve observed complaints, historical evidence, canonical records, and unresolved traceability. Hypotheses remain hypotheses; Challenger constraints and Unknowns remain visible. A failure chain can become incomplete without being rerouted or converted into a root-cause conclusion. Missing comparative evidence produces insufficient-evidence language.

## API and UI

Endpoints:

- `POST /api/v1/investigations/{investigation_id}/counterfactuals`
- `GET /api/v1/investigations/{investigation_id}/counterfactuals`
- `GET /api/v1/investigations/counterfactuals/{counterfactual_id}`

The Investigation Workspace includes a Constrained Counterfactual section with readable intervention controls, action feedback, baseline-versus-alternative presentation, limitations, provenance, and explicit hypothetical labeling. Decision Center remains human-governed and does not treat the result as evidence.

## Isolation and safety

Tenant filters are applied to investigation and persisted scenario lookup. The workspace applies Event/ Known temporal filters. Ground Truth is not imported into the runtime service. Source text is stored as request data and is not executed as instructions. ProductVersion context is retained in the baseline snapshot and no cross-product target is accepted.

## VS009 and known limitations

VS009 is represented by the controlled Component Rev B / candidate-change intervention pattern. The result weakens a candidate explanation while preserving pre-change complaints, incomplete traceability, and unavailable comparative testing as uncertainty. This is not a simulation, prediction, root-cause determination, or regulatory decision.

Manual browser validation remains pending and is tracked in `R1_DAY16_MANUAL_UI_VALIDATION_CHECKLIST.md`.

## Automated validation

- Day 16 targeted tests: 8 passed, 0 failed.
- Full regression: 196 passed, 0 failed, 0 errors, 2 warnings.
- Frontend production build: passed.
