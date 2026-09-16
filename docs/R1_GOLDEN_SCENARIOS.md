# MDARIX R1 Golden Scenarios

## Status

PROPOSED for Day 1 architecture freeze.

Each scenario specification must include purpose, input data, hidden ground truth, expected evidence, expected contradictions, expected unknowns, prohibited conclusion, expected system behavior, and acceptance criteria.

## Scenario IDs

### VS001 - Supplier Change Correlation

Purpose: detect a plausible supplier/component change correlation without overstating causality.

Expected behavior: leading hypothesis supported, contradictions retained, causality not claimed.

### VS002 - False Correlation

Purpose: prevent spurious temporal correlation from becoming a cause.

Expected behavior: evidence challenges correlation and recommends further review.

### VS003 - Missing Evidence

Purpose: identify missing records as unknowns.

Expected behavior: unknowns remain explicit and are not converted into assumptions.

### VS004 - Conflicting Evidence

Purpose: preserve and explain conflicting source records.

Expected behavior: contradictions are linked to hypotheses and brief.

### VS005 - Incorrect Timeline

Purpose: detect wrong event ordering or late-arriving evidence.

Expected behavior: temporal reconstruction flags inconsistency.

### VS006 - Shared Component Exposure

Purpose: identify exposure through shared components across products/lots.

Expected behavior: graph traversal links affected products without over-broad claims.

### VS007 - Premature Closure

Purpose: identify investigation closure despite unresolved contradictions or unknowns.

Expected behavior: AI Challenger and Investigation QA flag closure risk.

### VS008 - Control Failure

Purpose: evaluate whether control evidence supports or weakens a hypothesis.

Expected behavior: control relationship is evidence-linked.

### VS009 - Counterfactual

Purpose: test constrained scenario reasoning.

Expected behavior: assumptions and uncertainty are explicit.

### VS010 - AI Model Change

Purpose: validate AI provenance and reproducibility expectations across model changes.

Expected behavior: model/provider/version and prompt/template versions are recorded.

### VS011 - Multiple Causes

Purpose: maintain competing hypotheses.

Expected behavior: no premature single-cause selection.

### VS012 - Correct Abstention

Purpose: require abstention when evidence is insufficient.

Expected behavior: system reports unknowns and recommended next evidence instead of unsupported conclusion.
