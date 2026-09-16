# MDARIX R1 Retrieval Semantics

## Relevant

Evidence is relevant when it satisfies tenant scope, requested lifecycle context, temporal availability, source-anchor requirements, and either structured or semantic retrieval criteria.

## Structured Match

A structured match is evidence connected through deterministic metadata or `EvidenceEntityLink` records.

## Semantic Match

A semantic match is evidence whose chunk embedding is close to the query embedding. Semantic similarity alone is not enough when explicit lifecycle filters are supplied.

## Hybrid Match

A hybrid match is a deduplicated result retrieved by both structured and semantic mechanisms.

## Retrieval Score

Retrieval score means retrieval relevance only. It is not truth, confidence, evidence strength, causal probability, or regulatory significance.

## No Relevant Evidence

`NO_RELEVANT_EVIDENCE` means no tenant-scoped, context-valid evidence was retrieved.

## Insufficient Relevant Evidence

`INSUFFICIENT_RELEVANT_EVIDENCE` means the retrieval result is below the minimum relevance threshold or materially limited.

## Event-As-Of

Event-as-of asks what evidence relates to lifecycle reality that occurred or became effective by the requested time.

## Known-As-Of

Known-as-of asks what evidence was available to MDARIX by the requested time.

## Duplicate Result

A duplicate result is the same logical evidence chunk returned through multiple retrieval mechanisms. It is collapsed into one result.

## Contextual Evidence

Contextual evidence helps frame an investigation but does not prove causality.
