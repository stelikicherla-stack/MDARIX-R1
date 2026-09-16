# MDARIX R1 Source Contracts

## QMS Complaint V1

- Source: QMS
- Category: qms
- Format: CSV
- Mapping: `QMS_COMPLAINT_V1`
- File: `data/golden/source/qms/complaints.csv`
- Required fields: `complaint_id`, `complaint_identifier`, `product_version_id`, `event_timestamp`, `recorded_timestamp`, `ingestion_timestamp`, `failure_mode`, `narrative`
- Quality issues: missing lot reference, duplicate candidate, date without timezone

## QMS Investigation V1

- Source: QMS
- Format: CSV
- Mapping: `QMS_INVESTIGATION_V1`
- File: `data/golden/source/qms/investigations.csv`
- Required fields: `investigation_id`, `investigation_identifier`, `product_id`, `question`, `opened_at`, `status`

## PLM Product / Version / Component / Requirement / Change V1

- Source: PLM
- Format: CSV
- Mappings: `PLM_PRODUCT_V1`, `PLM_PRODUCT_VERSION_V1`, `PLM_COMPONENT_V1`, `PLM_REQUIREMENT_V1`, `PLM_CHANGE_V1`
- Files: `data/golden/source/plm/*.csv`
- Timestamp semantics: product version effective dates, change event dates, change effective dates
- Day 4 preserves revision strings and aliases without resolving them.

## ERP/MES Supplier / Site / Lot V1

- Source: ERP_MES
- Format: CSV
- Mappings: `ERP_SUPPLIER_V1`, `ERP_SITE_V1`, `ERP_LOT_V1`
- Files: `data/golden/source/erp_mes/*.csv`
- Quality issues: incomplete traceability and date-only timestamps
- Supplier aliases remain source representations.

## Evidence Metadata V1

- Source: EVIDENCE
- Format: JSON
- Mapping: `GENERIC_SOURCE_V1`
- File: `data/golden/source/documents/evidence_metadata.json`
- Day 4 preserves document metadata and timestamps for later evidence normalization.

## Evidence File V1

- Source: EVIDENCE
- Format: Markdown
- Mapping: `EVIDENCE_FILE_V1`
- Files: `data/golden/source/evidence/*.md`
- Required fields: `filename`, `relative_path`, `content`
- Day 4 registers and checksums evidence text. It does not run extraction AI.
