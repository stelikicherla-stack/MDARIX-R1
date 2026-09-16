# MDARIX R1 Golden Scenarios

## Status

IMPLEMENTED as `r1-day3-golden-v1` synthetic Golden Dataset foundation.

Ground Truth is stored under `evaluation/ground_truth/`. Application-facing canonical data under `data/golden/canonical/` intentionally excludes hidden answers, prohibited conclusions, and expected conclusions.

Each scenario specification must include purpose, input data, hidden ground truth, expected evidence, expected contradictions, expected unknowns, prohibited conclusion, expected system behavior, and acceptance criteria.

## Scenario IDs

### VS001 - Supplier Change Correlation

Purpose: detect a plausible supplier/component change correlation without overstating causality.

Expected behavior: leading hypothesis supported, contradictions retained, causality not claimed.

Implemented with AcmeCare Instruments, AsterFlow Rev D, NovaCap supplier process change, Component Rev B, affected lots, increased shutdown complaints, pre-Rev B shutdown complaints, a passed Rev B validation report, incomplete lot traceability, and missing comparative Rev A/Rev B testing.

### VS002 - False Correlation

Purpose: prevent spurious temporal correlation from becoming a cause.

Expected behavior: evidence challenges correlation and recommends further review.

Implemented through a packaging-label revision near the shutdown complaint increase with no plausible electrical mechanism.

### VS003 - Missing Evidence

Purpose: identify missing records as unknowns.

Expected behavior: unknowns remain explicit and are not converted into assumptions.

Implemented through unavailable comparative testing and incomplete lot genealogy.

### VS004 - Conflicting Evidence

Purpose: preserve and explain conflicting source records.

Expected behavior: contradictions are linked to hypotheses and brief.

Implemented through pre-Rev B shutdown complaints and a passed Rev B qualification artifact.

### VS005 - Incorrect Timeline

Purpose: detect wrong event ordering or late-arriving evidence.

Expected behavior: temporal reconstruction flags inconsistency.

Implemented through distinct event, recorded, and ingestion timestamps plus late-arriving lot genealogy evidence.

### VS006 - Shared Component Exposure

Purpose: identify exposure through shared components across products/lots.

Expected behavior: graph traversal links affected products without over-broad claims.

Implemented through reusable power-module/component records and lot/component traceability.

### VS007 - Premature Closure

Purpose: identify investigation closure despite unresolved contradictions or unknowns.

Expected behavior: AI Challenger and Investigation QA flag closure risk.

Implemented through a plausible historical closure note that did not address key contradictions.

### VS008 - Control Failure

Purpose: evaluate whether control evidence supports or weakens a hypothesis.

Expected behavior: control relationship is evidence-linked.

Implemented through controlled validation and process-control evidence artifacts.

### VS009 - Counterfactual

Purpose: test constrained scenario reasoning.

Expected behavior: assumptions and uncertainty are explicit.

Implemented as an evaluation scenario around Rev B absence and complaint pattern uncertainty.

### VS010 - AI Model Change

Purpose: validate AI provenance and reproducibility expectations across model changes.

Expected behavior: model/provider/version and prompt/template versions are recorded.

Implemented as an evidence/metadata fixture for later AI execution comparison.

### VS011 - Multiple Causes

Purpose: maintain competing hypotheses.

Expected behavior: no premature single-cause selection.

Implemented through shutdown subsets that include Rev B-aligned complaints and pre-existing connector-related complaints.

### VS012 - Correct Abstention

Purpose: require abstention when evidence is insufficient.

Expected behavior: system reports unknowns and recommended next evidence instead of unsupported conclusion.

Implemented through missing field operating conditions and unresolved comparative evidence.
