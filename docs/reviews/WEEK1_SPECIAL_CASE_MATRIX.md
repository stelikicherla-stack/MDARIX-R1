# Week 1 Special Case Matrix

| Case | Expected Existing Behavior | Evidence | Result |
| --- | --- | --- | --- |
| Multi-source disagreement | Preserve source values and avoid silent consensus | Staged records, source-canonical links, Day 5 tests | PASS |
| Historical state | Product versions and timeline preserve effective dates | Day 7 tests | PASS |
| Late-arriving information | Event time distinct from knowledge time | Day 7 tests, validator | PASS |
| Shared component | Graph/Product 360 can show component/supplier context without causal inference | Day 6/7 tests | PASS |
| Duplicate records | Idempotency and duplicate candidate preservation | Day 4/5 tests | PASS |
| Ambiguous identity | Requires review; no forced merge | Day 5 tests | PASS |
| Cross-tenant identical identifiers | Composite tenant constraints prevent cross-link | Day 2 tests | PASS |
| Missing lot traceability | Limitation remains visible | Day 7 tests | PASS |
| Missing evidence | Unknown/limitation preserved | Day 3/5 tests | PASS |
| Conflicting evidence | Supporting/contradicting evidence model remains distinct | Day 2/3 tests | PASS |
| False correlation | No causal conclusion generated | Day 6/7 tests | PASS |
| Multiple lifecycle branches | Product/version selection preserved | Day 7 tests | PASS |
| Correct abstention | No root-cause conclusion in deterministic Week 1 | Day 7 tests | PASS |
| Temporal boundary conditions | Known-as-of and event-as-of differ | Day 7 tests | PASS |
| Reprocessing/idempotency | Repeat ingestion/normalization remains deterministic | Day 4/5 tests | PASS |
