# Week 1 End-to-End Traceability

Primary trace path reviewed: AsterFlow 100 Rev D / VS001.

| Stage | Artifact | Evidence |
| --- | --- | --- |
| Source | PLM/QMS/ERP/Evidence files | `data/golden/source/**` |
| Ingestion | Staged raw/parsed/candidate payloads | `staged_source_records` |
| Quality | Warnings for missing lot, date-only timestamps, incomplete traceability | `data_quality_issues` |
| Canonical | Product, product version, component, supplier, lot, complaint, investigation, evidence | canonical tables |
| Identity | Source-canonical links | `source_canonical_links` |
| Relationships | Product-version-component, component-supplier, lot-version | `product_components`, `component_suppliers`, `canonical_relationships` |
| Reality Graph | Nodes and supported relationships | `graph/service.py` |
| Product 360 | Product-centric sections and limitations | `/api/v1/products/{id}/product-360` |
| Timeline | Event/effective/recorded/knowledge dimensions | `/api/v1/products/{id}/timeline` |
| UI | React Product 360 view | `frontend/src/main.tsx` |

Result: PASS. The review fixed the missing product-version-component link and verified Product 360 no longer depends on hardcoded component identifiers.
