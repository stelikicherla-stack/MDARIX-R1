# MDARIX R1 Hypothesis Contract

Primary schema: `hypothesis_engine.schemas.HypothesisSet`

## Hypothesis Fields

- `hypothesis_id`
- `investigation_id`
- `statement`
- `scope`
- `status`
- `related_objects`
- `supporting_evidence`
- `contradicting_evidence`
- `contextual_evidence`
- `unknowns`
- `assumptions`
- `temporal_consistency`
- `evidence_gaps`
- `falsification_conditions`
- `alternative_explanations`
- `source_references`
- `context_snapshot`
- `provenance`
- `human_review_status`

## Status Values

No status means proven cause.

Allowed status examples include `PROPOSED`, `UNDER_INVESTIGATION`, `MIXED_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, `REQUIRES_MORE_EVIDENCE`, and `NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS`.
