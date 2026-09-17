# R1 Day 13 AI Challenger Implementation

The controlled Challenger consumes the validated Day 12 `HypothesisSet`; it does not reconstruct reality from an unrestricted database dump. It emits typed `InvestigationChallenge` records with source references, materiality, temporal context, provenance, and explicit human-review state.

The rule-grounded engine detects evidence insufficiency, contradictions, temporal limits, causal leaps, assumptions, alternatives, and supported confounding context. A challenge is not a fact, root cause, or human decision. Prompt text is never policy, and persisted output excludes hidden chain-of-thought.

Persistence uses the existing tenant-scoped `AIExecution` audit path. API: `POST/GET /api/v1/investigations/{investigation_id}/challenges`.
