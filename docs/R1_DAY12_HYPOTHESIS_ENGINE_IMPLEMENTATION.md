# MDARIX R1 Day 12 Hypothesis Engine Implementation

Day 12 implements a controlled Competing Hypothesis Engine.

It consumes Day 11 validated `InvestigationAnalysis` and produces structured `HypothesisSet` output.

Hypotheses are explanations to test. They are not facts, root causes, human decisions, or regulatory determinations.

## Persistence

Day 12 reuses `AIExecution` for provenance and structured output. No schema migration is required for R1.

## API

- `POST /api/v1/investigations/{id}/hypotheses`
- `GET /api/v1/investigations/{id}/hypotheses`
- `GET /api/v1/investigations/{id}/hypotheses/{hypothesis_id}`

## UI

The Investigation Workspace includes a Competing Hypotheses section showing support, contradiction, context, gaps, temporal fit, falsification conditions, and validation metrics.
