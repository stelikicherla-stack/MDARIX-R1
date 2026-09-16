# Week 1 Edge Case Matrix

| Case ID | Source Day | Feature | Normal Scenario | Edge Condition | Expected Existing Behavior | Actual Behavior | Test | Result | Finding ID | Fix Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EC-001 | Day 0 | Docker DB | DB reachable | Container restart | Persistent data remains | Verified non-destructive status; no volume reset | Docker ps, validators | PASS |  |  |
| EC-002 | Day 0 | Environment | `.env` present | `.env` ignored | Not pushed | Remote tree scan clean | Git scan | PASS |  |  |
| EC-003 | Day 2 | Tenant FK | Same tenant links | Cross-tenant FK | Reject invalid link | Rejected by composite FK | Day 2 tests | PASS |  |  |
| EC-004 | Day 3 | Ground Truth | Evaluation assets exist | Runtime leakage | Rejected/excluded | Runtime code excludes GT | scans/tests | PASS |  |  |
| EC-005 | Day 4 | Ingestion | Valid CSV | Missing required field | Failed run with explicit issue | Explicit failure | Day 4 tests | PASS |  |  |
| EC-006 | Day 4 | Ingestion | First ingest | Duplicate ingest | Idempotent duplicate run | No duplicate staged rows | Day 4 tests | PASS |  |  |
| EC-007 | Day 5 | Identity | Exact ID | Ambiguous complaint | Human review / unresolved | Preserved | Day 5 tests | PASS |  |  |
| EC-008 | Day 5 | Configuration | Version has components | Missing materialized relationship | Must not hardcode | Fixed | Day 7 tests | PASS | W1R-HIGH-001 | FIXED |
| EC-009 | Day 6 | Graph | Connectivity path | Causality request | Reject unsupported relationship | Rejects `CAUSE` | Day 6 tests | PASS |  |  |
| EC-010 | Day 7 | Temporal | Current view | Known-as-of historical view | No future-known evidence | Fixed and tested | Day 7 tests | PASS | W1R-HIGH-002 | FIXED |
| EC-011 | Day 7 | Temporal | Current view | Event-as-of historical view | No future-effective sections | Fixed and tested | Day 7 tests | PASS | W1R-HIGH-002 | FIXED |
| EC-012 | Day 7 | UI/API | Product 360 load | Missing product | 404/controlled error | Implemented | API tests/manual smoke | PASS |  |  |
