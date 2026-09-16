# MDARIX R1 Identity Resolution Rules

## Rule Set

Rule set version: `day5.rules.v1`

Rules are deterministic and tenant-bound. No rule uses AI confidence, Ground Truth answers, hidden scenario labels, or similarity alone for authoritative matching.

## Implemented Rules

| Rule ID | Entity | Precedence | Purpose |
| --- | --- | ---: | --- |
| `PRODUCT_EXACT_ID_V1` | Product | 10 | Exact product identity from source product identifiers |
| `PRODUCT_VERSION_COMPOSITE_V1` | ProductVersion | 20 | Tenant + product + revision/version |
| `SOURCE_ALIAS_VERSION_V1` | ProductVersion | 30 | Approved source product-version aliases |
| `SUPPLIER_ALIAS_V1` | Supplier | 40 | Controlled supplier aliases |
| `COMPONENT_IDENTIFIER_REVISION_V1` | Component | 50 | Component identifier plus revision |
| `SITE_IDENTIFIER_V1` | ManufacturingSite | 60 | Controlled site identifier |
| `LOT_COMPOSITE_V1` | LotBatch | 70 | Lot identifier plus product-version and site context |
| `REQUIREMENT_IDENTIFIER_V1` | Requirement | 80 | Requirement identifier plus product context |
| `CHANGE_IDENTIFIER_V1` | Change | 90 | Explicit change identifier |
| `COMPLAINT_SOURCE_ID_V1` | Complaint | 100 | Exact complaint source identity |
| `INVESTIGATION_SOURCE_ID_V1` | Investigation | 110 | Exact investigation identity |
| `EVIDENCE_IDENTIFIER_V1` | Evidence | 120 | Evidence metadata/file identity |
| `RISK_IDENTIFIER_V1` | Risk | 130 | Exact risk identity |
| `FAILURE_MODE_IDENTIFIER_V1` | FailureMode | 140 | Exact failure mode identity |
| `CONTROL_IDENTIFIER_V1` | Control | 150 | Exact control identity |

## Ambiguity Behavior

Missing product or version context is not forced. Duplicate candidate complaints require human review. Similar complaint narratives remain distinct complaints.

## Provenance

Each link stores source system, source file, staged source record ID, mapping version, rule ID, normalized comparison value, resolution status, and `ground_truth_used=false`.

## Limitations

The rule set is intentionally conservative. It does not perform fuzzy supplier matching, narrative deduplication, causal inference, or graph traversal APIs.
