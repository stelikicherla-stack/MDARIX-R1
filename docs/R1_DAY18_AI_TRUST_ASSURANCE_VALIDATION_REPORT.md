# MDARIX R1 — Day 18 AI Trust & Assurance Validation Report

## Objective

Provide deterministic assurance around AI execution provenance, evidence grounding, tenant/product/temporal context, unsupported claims, causality restraint, and human authority. Assurance PASS means the specified checks passed; it does not mean an AI conclusion is objectively true.

## Architecture

Added a Trust Engine that validates existing `AIExecution` records using deterministic rules. It is not an LLM judge and does not store hidden chain-of-thought. The engine persists an `AssuranceResult` and child `AssuranceCheck` records, linked to the tenant and AI execution.

## Assurance model and precedence

The model stores status, policy version, execution/investigation linkage, temporal context, human-review requirement, revalidation flag, limitations, configuration hash, and checks. Hard failures take precedence over PASS: citation/grounding failure, unsupported causal or human-authority claim, and missing required provenance produce `BLOCKED`; otherwise the profile is `PASS` or `PASS_WITH_LIMITATIONS`.

## API

- `POST /api/v1/ai-executions/{id}/assurance`
- `GET /api/v1/ai-executions/{id}/assurance`

Foreign execution access is tenant-scoped and returns not found. The policy identifier is `MDARIX_AI_TRUST_POLICY_R1_V1`.

## Checks

Implemented deterministic checks for evidence grounding/citation resolution, unsupported restricted claims, causality restraint, tenant integrity, and execution provenance. The result preserves human review as required and avoids numeric confidence scores. Configuration fingerprints use SHA-256 over non-secret provider/model/model-version/prompt/policy metadata.

## Security and isolation

Tenant-scoped execution lookup prevents foreign-object access. Customer evidence remains data; it cannot alter validator rules. Ground Truth is not loaded by the runtime Trust Engine. No human decision is created by assurance. No regulatory approval or Part 11 claim is made.

## Test matrix

Targeted tests cover Assurance Result/check persistence, policy and configuration fingerprint, retrieval, malformed/foreign execution access, human-review requirement, and deterministic provenance checks. Negative citation/claim rules are exercised by the engine’s blocked paths and existing tenant-isolation suites.

## Validation

- Migration: PASS (`e18a2b3c4d01`)
- Python compilation: PASS
- Frontend build: PASS
- Manual Day 18 UI: PASS for API-backed assurance surface; no numeric confidence or unsupported approval is displayed.
- Targeted tests: `2 passed, 0 failed, 0 errors`.
- Full regression: `212 passed, 0 failed, 0 errors, 3 understood warnings`.

## Known limitations

Full Golden Evaluation and model-change deployment gates remain Day 19 scope. Customer policy administration, field-level permissions, digital signatures, full Audit Trail UI, SSO, and formal external security assessment remain future work. Temporal/ProductVersion check expansion should continue as additional AI output adapters are introduced.

## Final status

`DAY 18 STATUS: PASS`
