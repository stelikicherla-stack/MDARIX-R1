# R1 Day 14 Validation Report

Day 14 implementation includes typed Unknowns Radar and Failure Chain contracts, controlled engines, tenant-scoped persistence/API routes, gap preservation, contradiction/temporal metadata, and Day 15 handoff documentation. Focused semantic validation covers material unknown detection, deduplication, abstention, broken chains, epistemic link status, and graph-path safety.

Validation results: Day 12 + Day 13 + Day 14 focused suite **14 passed**. Complete available R1 regression: **182 passed, 0 failed, 0 errors** using a project-local pytest basetemp. Three dependency/cache warnings remain; they did not affect collection or execution.

The UI production build now passes, but manual UI validation is not claimed. Live database/API scenario validation remains blocked because Docker/PostgreSQL is unavailable in the environment. See `R1_WEEK2_LIVE_INTEGRATION_VALIDATION_REPORT.md`; the Day 14 hard exit gate remains open.
