# MDARIX R1 Day 12 Contract

Day 12 Hypothesis Engine receives validated Day 11 `InvestigationAnalysis`.

## Inputs

- `analysis_id`
- `investigation_id`
- `context_snapshot_id`
- `context_snapshot_version`
- `observations`
- `evidence_relationships`
- `possible_explanations`
- `contradictions`
- `missing_information`
- `questions_to_investigate`
- `limitations`
- `source_references`
- `temporal_context`
- `model_provenance`
- `validation_summary`

## Semantics

Possible explanations are not ranked truth.

Contradictions must remain visible.

Missing information is not negative evidence.

Historical source conclusions are source-attributed only.

## Failure Behavior

If Day 11 status is `FAILED_VALIDATION`, Day 12 must not use the analysis.

If status is `ABSTAINED_INSUFFICIENT_EVIDENCE`, Day 12 may create limited hypothesis scaffolding only if grounded sources exist.

## Boundary

Day 12 must not reconstruct investigation context from raw tables when a validated Day 11 analysis is available.
