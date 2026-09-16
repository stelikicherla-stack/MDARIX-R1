# MDARIX R1 Evaluation Strategy

## Status

PROPOSED for Day 1 architecture freeze.

## Golden Dataset Target

- 1 fictional medical-device company
- 2 product families
- 4 product versions
- 15-20 components
- 5 suppliers
- 2 manufacturing sites
- 15-20 lots
- 15-20 product/process changes
- 100-150 complaints
- 10 investigations
- Approximately 15 risks
- Approximately 15 failure modes
- 30-50 evidence documents

Include true correlations, false correlations, missing evidence, contradictory evidence, incorrect timelines, shared components, multiple plausible causes, premature closure, and situations requiring AI abstention.

## Quality Targets

- Temporal reconstruction: >=95% on controlled scenarios where ground truth exists
- Evidence grounding: 100% of material AI claims have evidence/provenance or are labeled inference/hypothesis/unknown
- Contradiction identification: >=90%
- Unknown identification: >=90%
- Failure-chain reconstruction: >=90%
- AI provenance: 100% of material AI executions
- Human approval: 100% for material regulated decisions
- Golden scenarios: minimum 7/12 passing by R1 exit
- End-to-end primary demo: PASS
- Critical defects: 0 open at release gate
- Cross-tenant leakage: 0

Do not fake metrics. If evaluation cannot measure something reliably, report that.

## Primary KPI

TIME-TO-DECISION.

Measurement architecture compares baseline investigation time with MDARIX-assisted investigation time.

## Secondary Measures

Evidence retrieval precision, timeline reconstruction accuracy, contradiction recall, unknown recall, hypothesis evidence coverage, unsupported claim rate, human override rate, AI latency, and brief generation time.
