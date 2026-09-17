# R1 Day 14 Unknowns Radar and Failure Chain Intelligence

Day 14 consumes controlled Day 12 hypotheses and Day 13 challenges. Unknowns are first-class typed records and remain distinct from false, negative, or absent facts. Failure chains are evidence-bounded candidate sequences whose links carry explicit epistemic status.

The implementation reuses tenant-scoped `AIExecution` persistence and exposes:

- `POST/GET /api/v1/investigations/{id}/unknowns`
- `POST/GET /api/v1/investigations/{id}/failure-chains`

Material gaps are propagated as `UNKNOWN_GAP`; contradictions and temporal limitations are retained. No autonomous root cause or human decision is produced.
