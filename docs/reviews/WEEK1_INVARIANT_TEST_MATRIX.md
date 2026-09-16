# Week 1 Invariant Test Matrix

| Invariant | Enforcement | Test / Scan | Result |
| --- | --- | --- | --- |
| No Ground Truth in runtime output | Ingestion rejects `evaluation/ground_truth`; runtime code does not read it | Day 3-7 tests, scans | PASS |
| No unsupported causal relationship | Relationship catalog and graph tests reject `CAUSE` | Day 5/6/7 tests | PASS |
| No invented evidence | Evidence sourced from staged metadata/files | Day 4/5/7 tests | PASS |
| No silent forced identity match | Ambiguous links marked for review/unresolved | Day 5 tests | PASS |
| Product-version configuration is source-backed | PLM product-component source, `product_components`, canonical relationship | Review tests | PASS |
| Known-as-of excludes future knowledge | Product 360 and timeline filters | Review tests | PASS |
| Event-as-of excludes future effective/event rows | Product 360 and timeline filters | Review tests | PASS |
| Tenant scope is preserved | Composite FK/unique constraints and tenant-scoped service queries | Day 2/6/7 tests | PASS |
| Source truth remains recoverable | Staged raw payload and source-canonical provenance | Day 4/5 tests | PASS |
| Week 1 uses no material AI inference | No AI runtime invocation | Code scan | PASS |
