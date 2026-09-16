# MDARIX R1 Investigation Analysis Contract

Primary schema: `investigator.schemas.InvestigationAnalysis`

## Required Fields

- `analysis_id`
- `investigation_id`
- `context_snapshot_id`
- `context_snapshot_version`
- `ai_execution_id`
- `status`
- `observations`
- `relevant_changes`
- `temporal_patterns`
- `evidence_relationships`
- `possible_explanations`
- `contradictions`
- `missing_information`
- `questions_to_investigate`
- `limitations`
- `rejected_items`
- `source_references`
- `temporal_context`
- `model_provenance`
- `validation_summary`
- `guardrails`
- `created_at`

## Statement Types

- `OBSERVATION`
- `DETERMINISTIC_RELATIONSHIP`
- `SOURCE_ATTRIBUTED_CONCLUSION`
- `POSSIBLE_EXPLANATION`
- `CONTRADICTION`
- `MISSING_INFORMATION`
- `INVESTIGATIVE_QUESTION`
- `LIMITATION`
- `TEMPORAL_PATTERN`
- `ASSUMPTION`
- `INSUFFICIENT_EVIDENCE`

## Grounding Status Values

- `ACCEPTED`
- `REJECTED_UNGROUNDED`
- `INSUFFICIENT_EVIDENCE`
- `REQUIRES_REVIEW`

## Analysis Status Values

- `COMPLETED`
- `COMPLETED_WITH_LIMITATIONS`
- `ABSTAINED_INSUFFICIENT_EVIDENCE`
- `FAILED_VALIDATION`

## Day 12 Consumption

Day 12 should consume validated `possible_explanations`, `contradictions`, `missing_information`, `questions_to_investigate`, `source_references`, and `temporal_context`.

Day 12 must not rerun Day 11 from raw data.
