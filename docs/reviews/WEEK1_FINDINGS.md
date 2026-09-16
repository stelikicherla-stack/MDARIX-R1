# Week 1 Findings

## HIGH

### W1R-HIGH-001 - Product 360 Configuration Was Hardcoded Instead Of Relationship-Derived

Severity: HIGH

Source Day: Day 5, Day 7

Requirement: Product 360 configuration must reflect canonical product-version/component relationships with provenance.

Observed Behavior: `Product360Service.components` included a hardcoded fallback for `COMP-PWR`, `COMP-CAP`, `COMP-FW`, and `COMP-CONN`; `product_components` contained zero rows.

Expected Behavior: Configuration is derived from deterministic source/canonical relationships.

Evidence: Focused review test failed before fix with missing components after removing hardcoded fallback; database count showed `product_components=0`.

Impact: Product 360 could present configuration that was not traceable to source/canonical relationships.

Reproduction Steps: Query Product 360 Rev D after removing fallback, or query `SELECT count(*) FROM product_components`.

Root Technical Cause: Day 5 did not ingest/materialize product-version component membership even though the schema and Product 360 contract required it.

Fix Required: Yes.

Scope Classification: IN-SCOPE WEEK-1.

Files Affected: `data/golden/source/plm/product_components.csv`, `ingestion/mappings/plm_product_component_v1.json`, `ingestion/services/ingestion_service.py`, `ingestion/normalization/service.py`, `backend/app/product360/service.py`, `tests/test_day7_product360_temporal.py`.

Tests Required: Day 3-Day 5 affected tests, Day 7 tests, validators, full regression.

Retest Result: Day 7 focused suite `20 passed`; Day 3-Day 5 affected suite `64 passed`.

Final Status: FIXED.

### W1R-HIGH-002 - Product 360 As-Of Views Filtered Timeline But Not Section Payloads

Severity: HIGH

Source Day: Day 7

Requirement: Historical/as-of views must not leak future/current section data.

Observed Behavior: Timeline events were filtered, but `complaints`, `evidence`, `changes`, `lots`, `investigations`, and version lists were returned unfiltered in Product 360 payloads.

Expected Behavior: Section payloads use the same known/event temporal semantics as timeline.

Evidence: Code review of `Product360Service.product360`.

Impact: UI/API could show future-known evidence or current state in historical views.

Reproduction Steps: Request Product 360 with `mode=known&as_of=2026-02-15T00:00:00Z` and inspect evidence/complaint arrays.

Root Technical Cause: Temporal filtering was applied only after timeline construction.

Fix Required: Yes.

Scope Classification: IN-SCOPE WEEK-1.

Files Affected: `backend/app/product360/service.py`, `tests/test_day7_product360_temporal.py`.

Tests Required: Known-as-of and event-as-of Product 360 section tests.

Retest Result: Day 7 focused suite `20 passed`.

Final Status: FIXED.

## MEDIUM

None unresolved.

## LOW

None unresolved.

## INFORMATIONAL

- Date-only source timestamps are preserved and flagged as `DATE_WITHOUT_TIMEZONE`; this is expected for the controlled Golden Dataset.

## OUT-OF-SCOPE OBSERVATIONS

See `WEEK1_OUT_OF_SCOPE_OBSERVATIONS.md`.
