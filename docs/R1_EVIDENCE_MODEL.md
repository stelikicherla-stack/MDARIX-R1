# MDARIX R1 Evidence Model

## Status

PROPOSED for Day 1 architecture freeze.

## Principle

Evidence is a first-class object. Unsupported narrative statements are prohibited.

## Evidence Fields

Evidence supports evidence type, source, document/reference, extraction, relevant excerpt/reference, timestamp, related lifecycle object, reliability/data-quality indicator, support relationship, contradiction relationship, and provenance.

## Concept Boundaries

- Fact: validated source or derived fact.
- Evidence: material artifact or record supporting or contradicting a claim.
- Inference: reasoned interpretation grounded in evidence.
- Hypothesis: possible explanation under investigation.
- Unknown: missing, incomplete, or unresolved information.
- Decision: authorized human disposition.

## Hypotheses

Investigations may contain multiple competing hypotheses. Each hypothesis records statement, status, supporting evidence, contradicting evidence, unknowns, strength indicator, creation source, AI/human origin, reviewer disposition, and timestamps.

Do not design MDARIX to select a cause prematurely.

## Unknowns

Unknowns are first-class investigation objects and must not be silently converted into assumptions.

## Failure Chains

Failure chains represent possible causal paths. Each connection requires evidence/provenance or must be marked hypothetical.

## Counterfactual Boundary

R1 counterfactual analysis is constrained. Outputs state assumptions, cite evidence, state uncertainty, and avoid presenting speculation as fact.
