# MDARIX R1 AI Architecture

## Status

PROPOSED for Day 1 architecture freeze.

## Principle

Use maximum appropriate intelligence. Do not maximize AI count.

Use deterministic code/rules for calculations, identity logic, timestamps, data validation, permissions, deterministic regulatory/business rules, and integrity checks.

Use generative AI for evidence extraction, summarization, reasoning support, hypothesis generation, contradiction explanation, investigation narrative, and brief drafting.

Use agentic AI only for controlled investigation orchestration.

Evolutionary or genetic optimization is excluded unless a concrete R1 optimization problem later requires large candidate-space search.

## Orchestration

R1 uses one controlled orchestrator with logical specialists:

- Retrieval
- Timeline
- Evidence
- Hypothesis
- Challenger
- Unknowns
- Failure Chain
- Brief

Each specialist is a callable service/tool boundary. Orchestration must be observable, auditable, and constrained by tenant, investigation, user, and evidence context.

## Material Output Requirements

Every material AI output must be evidence grounded, attributable, versioned, auditable, reviewable, and reproducible where practical.

## AI Provenance

Material AI executions retain AI execution ID, tenant, user/requestor, investigation, model/provider, model version where available, prompt/template version, orchestration version, context references, evidence references, tools invoked, structured input, structured output, confidence/uncertainty, validation status, human reviewer, human disposition, execution timestamp, latency, and error state.

Hidden chain-of-thought must not be stored. Store business-relevant reasoning artifacts, structured rationale, evidence references, and provenance.

## Human Governance

AI recommends. Authorized humans decide. Final regulatory, safety, CAPA, recall, product release, risk acceptance, and investigation closure decisions require human review.
