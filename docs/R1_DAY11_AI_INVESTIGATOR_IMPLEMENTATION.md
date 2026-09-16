# MDARIX R1 Day 11 AI Investigator Implementation

## Scope

Day 11 implements a bounded Evidence-Grounded AI Investigator.

It consumes the Day 10 `InvestigationWorkspaceResponse` contract and produces validated structured `InvestigationAnalysis` output.

It does not declare root cause, establish causality, make regulatory decisions, close investigations, approve CAPA, or automate recall/reportability decisions.

## Runtime Flow

1. API receives investigation analysis request.
2. Service obtains Day 10 Investigation Workspace context.
3. Controlled investigator provider produces structured analysis items.
4. Grounding validator checks material statements.
5. Validated analysis is persisted through `AIExecution`.
6. API returns structured analysis only.

## Provider

Provider: `mdarix-controlled-investigator`

Model: `mdarix-rule-grounded-investigator`

Version: `1.0`

This local controlled provider preserves R1 safety behavior without sending uncontrolled full database context to an external model.

## Persistence

No new migration is required. Day 11 reuses `AIExecution`:

- `context_refs`: Day 10 context snapshot metadata
- `evidence_refs`: evidence identifiers and retrieval query references
- `structured_input`: request controls
- `structured_output`: validated `InvestigationAnalysis`
- `validation_status`: analysis status

Hidden chain-of-thought is not persisted.

## API

- `POST /api/v1/investigations/{investigation_id}/analysis`
- `GET /api/v1/investigations/{investigation_id}/analysis/latest`
- `GET /api/v1/investigations/{investigation_id}/analysis/{analysis_id}`

## UI

The Product 360 / Investigation Workspace panel includes a controlled `Run Analysis` action and structured sections for observations, possible explanations, contradictory evidence, missing information, questions, and validation/provenance.

It is not a chatbot.

## Guardrails

- Human authority remains required
- Retrieval rank is not evidence strength
- Graph connectivity is not causality
- Evidence content is untrusted data
- Abstention is successful when evidence is insufficient
