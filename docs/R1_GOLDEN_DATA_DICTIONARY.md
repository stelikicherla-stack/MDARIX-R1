# MDARIX R1 Golden Data Dictionary

## Notice

MDARIX R1 GOLDEN DATASET - SYNTHETIC TEST DATA ONLY. NOT FOR CLINICAL OR REGULATORY USE.

## Identifier Strategy

- `tenant_id`: fictional tenant identity.
- `product_id`: canonical product ID.
- `product_version_id`: canonical product version ID.
- `component_id`: canonical component ID.
- `lot_id`: canonical lot/batch ID.
- `complaint_id`: canonical complaint ID.
- `evidence_id`: canonical evidence artifact ID.
- Source identifiers remain separate from canonical IDs.

## Source Fields

- `source_product_version`: intentionally inconsistent source-system product version value.
- `source`: synthetic system or document source.
- `document_path`: relative path to concise synthetic evidence text.
- `data_quality_status`: controlled source-quality state.

## Temporal Fields

- `event_timestamp`: when an event occurred.
- `effective_timestamp`: when a change or version became effective.
- `recorded_timestamp`: when a source system recorded the item.
- `ingestion_timestamp`: when MDARIX would receive the record.
- `manufactured_timestamp`: when a synthetic lot was manufactured.

## Scenario Fields

- `scenario_id`: VS001 through VS012.
- `investigation_id`: canonical investigation associated with the scenario.
- `intentional_anomalies`: controlled imperfections used for evaluation.

## Controlled Vocabularies

### Evidence Quality

- `higher`
- `uncertain`

### Data Quality Status

- `reviewed`
- `missing_lot`
- `duplicate_candidate`
- `incomplete`

### Failure Modes

Examples include `shutdown`, `delayed_restart`, `false_alarm`, `connector_intermittency`, and `no_fault_found`.

### Anomaly Types

- `identity_variation`
- `supplier_alias`
- `missing_traceability`
- `delayed_record_entry`
- `duplicate_candidate`
- `late_arriving_evidence`
- `false_correlation`
- `multiple_causes`

## Canonical Mapping

Source data is intentionally fragmented across QMS-like, PLM-like, ERP/MES-like, and document/evidence sources. Canonical JSON maps these source records to product-centered MDARIX R1 entities but does not expose Ground Truth answers.

## Ground Truth Separation

Fields such as `hidden_ground_truth`, `expected_system_behavior`, and `prohibited_conclusions` are evaluation-only and appear under `evaluation/ground_truth/`, not application-facing canonical data.
