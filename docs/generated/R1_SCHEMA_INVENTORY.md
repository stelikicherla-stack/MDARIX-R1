# MDARIX R1 Day 2 Schema Inventory

## ai_executions

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NULL
- `requestor_ref`: `VARCHAR(255)` NULL
- `provider`: `VARCHAR(80)` NOT NULL
- `model_name`: `VARCHAR(120)` NOT NULL
- `model_version`: `VARCHAR(120)` NULL
- `prompt_template_version`: `VARCHAR(120)` NULL
- `orchestration_version`: `VARCHAR(120)` NULL
- `context_refs`: `JSONB` NULL
- `evidence_refs`: `JSONB` NULL
- `tools_invoked`: `JSONB` NULL
- `structured_input`: `JSONB` NULL
- `structured_output`: `JSONB` NULL
- `rationale_summary`: `TEXT` NULL
- `confidence_label`: `VARCHAR(80)` NULL
- `validation_status`: `VARCHAR(80)` NULL
- `execution_timestamp`: `TIMESTAMP` NOT NULL
- `latency_ms`: `INTEGER` NULL
- `error_state`: `TEXT` NULL

Primary key: `id`

### Foreign Keys
- `fk_ai_executions_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_ai_executions_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_ai_executions_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_ai_executions_tenant_id_id`: `tenant_id, id` unique=True

## alembic_version

### Columns
- `version_num`: `VARCHAR(32)` NOT NULL

Primary key: `version_num`

## audit_events

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `actor_ref`: `VARCHAR(255)` NULL
- `action`: `VARCHAR(120)` NOT NULL
- `entity_type`: `VARCHAR(120)` NOT NULL
- `entity_id`: `UUID` NULL
- `correlation_id`: `VARCHAR(120)` NULL
- `details`: `JSONB` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_audit_events_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

## changes

### Columns
- `change_identifier`: `VARCHAR(120)` NOT NULL
- `change_type`: `VARCHAR(80)` NOT NULL
- `description`: `TEXT` NOT NULL
- `event_timestamp`: `TIMESTAMP` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_changes_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_changes_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_changes_tenant_id_id`: `tenant_id, id`
- `uq_changes_tenant_identifier`: `tenant_id, change_identifier`

### Indexes
- `uq_changes_tenant_id_id`: `tenant_id, id` unique=True
- `uq_changes_tenant_identifier`: `tenant_id, change_identifier` unique=True

## complaints

### Columns
- `complaint_identifier`: `VARCHAR(120)` NOT NULL
- `product_id`: `UUID` NULL
- `product_version_id`: `UUID` NULL
- `lot_batch_id`: `UUID` NULL
- `event_timestamp`: `TIMESTAMP` NULL
- `complaint_timestamp`: `TIMESTAMP` NULL
- `description`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'open'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_complaints_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_complaints_tenant_id_lot_batches`: `tenant_id, lot_batch_id` -> `lot_batches(tenant_id, id)`
- `fk_complaints_tenant_id_product_versions`: `tenant_id, product_version_id` -> `product_versions(tenant_id, id)`
- `fk_complaints_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_complaints_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_complaints_tenant_id_id`: `tenant_id, id`
- `uq_complaints_tenant_identifier`: `tenant_id, complaint_identifier`

### Indexes
- `ix_complaints_tenant_product_event`: `tenant_id, product_id, event_timestamp` unique=False
- `uq_complaints_tenant_id_id`: `tenant_id, id` unique=True
- `uq_complaints_tenant_identifier`: `tenant_id, complaint_identifier` unique=True

## component_suppliers

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `component_id`: `UUID` NOT NULL
- `supplier_id`: `UUID` NOT NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `evidence_id`: `UUID` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_component_suppliers_tenant_id_components`: `tenant_id, component_id` -> `components(tenant_id, id)`
- `fk_component_suppliers_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_component_suppliers_tenant_id_suppliers`: `tenant_id, supplier_id` -> `suppliers(tenant_id, id)`
- `fk_component_suppliers_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_component_suppliers_component_supplier`: `tenant_id, component_id, supplier_id`

### Indexes
- `uq_component_suppliers_component_supplier`: `tenant_id, component_id, supplier_id` unique=True

## components

### Columns
- `component_identifier`: `VARCHAR(120)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `revision`: `VARCHAR(80)` NULL
- `description`: `TEXT` NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_components_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_components_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_components_tenant_id_id`: `tenant_id, id`
- `uq_components_tenant_identifier_revision`: `tenant_id, component_identifier, revision`

### Indexes
- `ix_components_tenant_identifier`: `tenant_id, component_identifier` unique=False
- `uq_components_tenant_id_id`: `tenant_id, id` unique=True
- `uq_components_tenant_identifier_revision`: `tenant_id, component_identifier, revision` unique=True

## controls

### Columns
- `control_identifier`: `VARCHAR(120)` NOT NULL
- `control_type`: `VARCHAR(80)` NULL
- `description`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_controls_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_controls_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_controls_tenant_id_id`: `tenant_id, id`
- `uq_controls_tenant_identifier`: `tenant_id, control_identifier`

### Indexes
- `uq_controls_tenant_id_id`: `tenant_id, id` unique=True
- `uq_controls_tenant_identifier`: `tenant_id, control_identifier` unique=True

## decisions

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `decision_identifier`: `VARCHAR(120)` NOT NULL
- `decision_type`: `VARCHAR(80)` NOT NULL
- `disposition`: `VARCHAR(80)` NOT NULL
- `rationale`: `TEXT` NOT NULL
- `decision_timestamp`: `TIMESTAMP` NOT NULL
- `authorized_by_ref`: `VARCHAR(255)` NOT NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_decisions_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_decisions_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_decisions_tenant_id_id`: `tenant_id, id`
- `uq_decisions_tenant_identifier`: `tenant_id, decision_identifier`

### Indexes
- `uq_decisions_tenant_id_id`: `tenant_id, id` unique=True
- `uq_decisions_tenant_identifier`: `tenant_id, decision_identifier` unique=True

## evidence

### Columns
- `evidence_identifier`: `VARCHAR(120)` NOT NULL
- `investigation_id`: `UUID` NULL
- `evidence_type`: `VARCHAR(80)` NOT NULL
- `title`: `VARCHAR(255)` NOT NULL
- `source_reference`: `TEXT` NULL
- `document_ref`: `TEXT` NULL
- `extracted_text_ref`: `TEXT` NULL
- `reliability_status`: `VARCHAR(40)` NOT NULL 'unreviewed'::character varying
- `fact_type`: `VARCHAR(40)` NOT NULL 'source_fact'::character varying
- `content`: `TEXT` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_evidence_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_evidence_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_evidence_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_evidence_tenant_id_id`: `tenant_id, id`
- `uq_evidence_tenant_identifier`: `tenant_id, evidence_identifier`

### Indexes
- `ix_evidence_tenant_investigation`: `tenant_id, investigation_id` unique=False
- `uq_evidence_tenant_id_id`: `tenant_id, id` unique=True
- `uq_evidence_tenant_identifier`: `tenant_id, evidence_identifier` unique=True

## evidence_embeddings

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `evidence_id`: `UUID` NOT NULL
- `embedding_model`: `VARCHAR(120)` NOT NULL
- `embedding_vector_ref`: `VARCHAR(255)` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `embedding`: `NULL` NULL

Primary key: `id`

### Foreign Keys
- `fk_evidence_embeddings_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_evidence_embeddings_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Indexes
- `ix_evidence_embeddings_embedding_hnsw`: `embedding` unique=False

## failure_chain_edges

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `failure_chain_id`: `UUID` NOT NULL
- `from_node_id`: `UUID` NOT NULL
- `to_node_id`: `UUID` NOT NULL
- `edge_status`: `VARCHAR(40)` NOT NULL
- `evidence_id`: `UUID` NULL
- `rationale`: `TEXT` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_failure_chain_edges_from_node`: `tenant_id, from_node_id` -> `failure_chain_nodes(tenant_id, id)`
- `fk_failure_chain_edges_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_failure_chain_edges_tenant_id_failure_chains`: `tenant_id, failure_chain_id` -> `failure_chains(tenant_id, id)`
- `fk_failure_chain_edges_tenant_id_tenants`: `tenant_id` -> `tenants(id)`
- `fk_failure_chain_edges_to_node`: `tenant_id, to_node_id` -> `failure_chain_nodes(tenant_id, id)`

## failure_chain_nodes

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `failure_chain_id`: `UUID` NOT NULL
- `sequence_number`: `INTEGER` NOT NULL
- `node_type`: `VARCHAR(80)` NOT NULL
- `label`: `VARCHAR(255)` NOT NULL
- `lifecycle_object_type`: `VARCHAR(120)` NULL
- `lifecycle_object_id`: `UUID` NULL
- `evidence_id`: `UUID` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_failure_chain_nodes_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_failure_chain_nodes_tenant_id_failure_chains`: `tenant_id, failure_chain_id` -> `failure_chains(tenant_id, id)`
- `fk_failure_chain_nodes_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_failure_chain_nodes_sequence`: `tenant_id, failure_chain_id, sequence_number`
- `uq_failure_chain_nodes_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_failure_chain_nodes_sequence`: `tenant_id, failure_chain_id, sequence_number` unique=True
- `uq_failure_chain_nodes_tenant_id_id`: `tenant_id, id` unique=True

## failure_chains

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'draft'::character varying
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_failure_chains_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_failure_chains_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_failure_chains_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_failure_chains_tenant_id_id`: `tenant_id, id` unique=True

## failure_modes

### Columns
- `failure_mode_identifier`: `VARCHAR(120)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `description`: `TEXT` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_failure_modes_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_failure_modes_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_failure_modes_tenant_id_id`: `tenant_id, id`
- `uq_failure_modes_tenant_identifier`: `tenant_id, failure_mode_identifier`

### Indexes
- `uq_failure_modes_tenant_id_id`: `tenant_id, id` unique=True
- `uq_failure_modes_tenant_identifier`: `tenant_id, failure_mode_identifier` unique=True

## human_reviews

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `ai_execution_id`: `UUID` NULL
- `decision_id`: `UUID` NULL
- `reviewer_ref`: `VARCHAR(255)` NOT NULL
- `disposition`: `VARCHAR(80)` NOT NULL
- `comments`: `TEXT` NULL
- `review_timestamp`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_human_reviews_tenant_id_ai_executions`: `tenant_id, ai_execution_id` -> `ai_executions(tenant_id, id)`
- `fk_human_reviews_tenant_id_decisions`: `tenant_id, decision_id` -> `decisions(tenant_id, id)`
- `fk_human_reviews_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_human_reviews_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_human_reviews_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_human_reviews_tenant_id_id`: `tenant_id, id` unique=True

## hypotheses

### Columns
- `investigation_id`: `UUID` NOT NULL
- `statement`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'proposed'::character varying
- `origin`: `VARCHAR(20)` NOT NULL
- `reviewer_disposition`: `VARCHAR(80)` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_hypotheses_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_hypotheses_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_hypotheses_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_hypotheses_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_hypotheses_tenant_id_id`: `tenant_id, id` unique=True

## hypothesis_evidence

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `hypothesis_id`: `UUID` NOT NULL
- `evidence_id`: `UUID` NOT NULL
- `relation_type`: `VARCHAR(20)` NOT NULL
- `rationale`: `TEXT` NULL
- `created_by_type`: `VARCHAR(20)` NOT NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_hypothesis_evidence_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_hypothesis_evidence_tenant_id_hypotheses`: `tenant_id, hypothesis_id` -> `hypotheses(tenant_id, id)`
- `fk_hypothesis_evidence_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Indexes
- `ix_hypothesis_evidence_relation`: `tenant_id, hypothesis_id, relation_type` unique=False

## investigation_complaints

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `complaint_id`: `UUID` NOT NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_investigation_complaints_tenant_id_complaints`: `tenant_id, complaint_id` -> `complaints(tenant_id, id)`
- `fk_investigation_complaints_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_investigation_complaints_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_investigation_complaints_pair`: `tenant_id, investigation_id, complaint_id`

### Indexes
- `uq_investigation_complaints_pair`: `tenant_id, investigation_id, complaint_id` unique=True

## investigation_evidence

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `evidence_id`: `UUID` NOT NULL
- `relevance`: `TEXT` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_investigation_evidence_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_investigation_evidence_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_investigation_evidence_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_investigation_evidence_pair`: `tenant_id, investigation_id, evidence_id`

### Indexes
- `uq_investigation_evidence_pair`: `tenant_id, investigation_id, evidence_id` unique=True

## investigations

### Columns
- `investigation_identifier`: `VARCHAR(120)` NOT NULL
- `product_id`: `UUID` NOT NULL
- `investigation_question`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'open'::character varying
- `opened_at`: `TIMESTAMP` NULL
- `closed_at`: `TIMESTAMP` NULL
- `owner_ref`: `VARCHAR(255)` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_investigations_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_investigations_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_investigations_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_investigations_tenant_id_id`: `tenant_id, id`
- `uq_investigations_tenant_identifier`: `tenant_id, investigation_identifier`

### Indexes
- `ix_investigations_tenant_product`: `tenant_id, product_id` unique=False
- `uq_investigations_tenant_id_id`: `tenant_id, id` unique=True
- `uq_investigations_tenant_identifier`: `tenant_id, investigation_identifier` unique=True

## lot_batches

### Columns
- `lot_identifier`: `VARCHAR(120)` NOT NULL
- `product_version_id`: `UUID` NULL
- `manufacturing_site_id`: `UUID` NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_lot_batches_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_lot_batches_tenant_id_manufacturing_sites`: `tenant_id, manufacturing_site_id` -> `manufacturing_sites(tenant_id, id)`
- `fk_lot_batches_tenant_id_product_versions`: `tenant_id, product_version_id` -> `product_versions(tenant_id, id)`
- `fk_lot_batches_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_lot_batches_tenant_id_id`: `tenant_id, id`
- `uq_lots_tenant_lot_identifier`: `tenant_id, lot_identifier`

### Indexes
- `uq_lot_batches_tenant_id_id`: `tenant_id, id` unique=True
- `uq_lots_tenant_lot_identifier`: `tenant_id, lot_identifier` unique=True

## lot_components

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `lot_batch_id`: `UUID` NOT NULL
- `component_id`: `UUID` NOT NULL
- `evidence_id`: `UUID` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_lot_components_tenant_id_components`: `tenant_id, component_id` -> `components(tenant_id, id)`
- `fk_lot_components_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_lot_components_tenant_id_lot_batches`: `tenant_id, lot_batch_id` -> `lot_batches(tenant_id, id)`
- `fk_lot_components_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

## manufacturing_sites

### Columns
- `site_identifier`: `VARCHAR(120)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `location`: `VARCHAR(255)` NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_manufacturing_sites_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_manufacturing_sites_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_manufacturing_sites_tenant_id_id`: `tenant_id, id`
- `uq_sites_tenant_site_identifier`: `tenant_id, site_identifier`

### Indexes
- `uq_manufacturing_sites_tenant_id_id`: `tenant_id, id` unique=True
- `uq_sites_tenant_site_identifier`: `tenant_id, site_identifier` unique=True

## product_components

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `product_version_id`: `UUID` NOT NULL
- `component_id`: `UUID` NOT NULL
- `relationship_status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `effective_timestamp`: `TIMESTAMP` NULL
- `evidence_id`: `UUID` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_product_components_tenant_id_components`: `tenant_id, component_id` -> `components(tenant_id, id)`
- `fk_product_components_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_product_components_tenant_id_product_versions`: `tenant_id, product_version_id` -> `product_versions(tenant_id, id)`
- `fk_product_components_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_product_components_version_component`: `tenant_id, product_version_id, component_id`

### Indexes
- `uq_product_components_version_component`: `tenant_id, product_version_id, component_id` unique=True

## product_suppliers

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `product_id`: `UUID` NOT NULL
- `supplier_id`: `UUID` NOT NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `evidence_id`: `UUID` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_product_suppliers_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_product_suppliers_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_product_suppliers_tenant_id_suppliers`: `tenant_id, supplier_id` -> `suppliers(tenant_id, id)`
- `fk_product_suppliers_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

## product_versions

### Columns
- `product_id`: `UUID` NOT NULL
- `version_identifier`: `VARCHAR(120)` NOT NULL
- `description`: `TEXT` NULL
- `lifecycle_status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `release_timestamp`: `TIMESTAMP` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_product_versions_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_product_versions_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_product_versions_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_product_versions_tenant_id_id`: `tenant_id, id`
- `uq_product_versions_tenant_product_version`: `tenant_id, product_id, version_identifier`

### Indexes
- `ix_product_versions_tenant_product`: `tenant_id, product_id` unique=False
- `uq_product_versions_tenant_id_id`: `tenant_id, id` unique=True
- `uq_product_versions_tenant_product_version`: `tenant_id, product_id, version_identifier` unique=True

## products

### Columns
- `product_identifier`: `VARCHAR(120)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `description`: `TEXT` NULL
- `lifecycle_status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `product_family`: `VARCHAR(120)` NULL
- `manufacturer_context`: `VARCHAR(255)` NULL
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_products_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_products_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_products_tenant_id_id`: `tenant_id, id`
- `uq_products_tenant_product_identifier`: `tenant_id, product_identifier`

### Indexes
- `ix_products_tenant_product_identifier`: `tenant_id, product_identifier` unique=False
- `uq_products_tenant_id_id`: `tenant_id, id` unique=True
- `uq_products_tenant_product_identifier`: `tenant_id, product_identifier` unique=True

## reality_relationships

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_entity_type`: `VARCHAR(120)` NOT NULL
- `source_entity_id`: `UUID` NOT NULL
- `target_entity_type`: `VARCHAR(120)` NOT NULL
- `target_entity_id`: `UUID` NOT NULL
- `relationship_type`: `VARCHAR(120)` NOT NULL
- `assertion_status`: `VARCHAR(40)` NOT NULL 'supported'::character varying
- `evidence_id`: `UUID` NULL
- `confidence_label`: `VARCHAR(80)` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `provenance`: `JSONB` NULL
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_reality_relationships_tenant_id_evidence`: `tenant_id, evidence_id` -> `evidence(tenant_id, id)`
- `fk_reality_relationships_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Indexes
- `ix_reality_relationship_lookup`: `tenant_id, source_entity_type, source_entity_id` unique=False

## requirements

### Columns
- `product_id`: `UUID` NULL
- `product_version_id`: `UUID` NULL
- `requirement_identifier`: `VARCHAR(120)` NOT NULL
- `requirement_type`: `VARCHAR(80)` NULL
- `text`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_requirements_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_requirements_tenant_id_product_versions`: `tenant_id, product_version_id` -> `product_versions(tenant_id, id)`
- `fk_requirements_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_requirements_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_requirements_tenant_id_id`: `tenant_id, id`
- `uq_requirements_tenant_identifier`: `tenant_id, requirement_identifier`

### Indexes
- `uq_requirements_tenant_id_id`: `tenant_id, id` unique=True
- `uq_requirements_tenant_identifier`: `tenant_id, requirement_identifier` unique=True

## risks

### Columns
- `risk_identifier`: `VARCHAR(120)` NOT NULL
- `product_id`: `UUID` NULL
- `product_version_id`: `UUID` NULL
- `description`: `TEXT` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_risks_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_risks_tenant_id_product_versions`: `tenant_id, product_version_id` -> `product_versions(tenant_id, id)`
- `fk_risks_tenant_id_products`: `tenant_id, product_id` -> `products(tenant_id, id)`
- `fk_risks_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_risks_tenant_id_id`: `tenant_id, id`
- `uq_risks_tenant_identifier`: `tenant_id, risk_identifier`

### Indexes
- `uq_risks_tenant_id_id`: `tenant_id, id` unique=True
- `uq_risks_tenant_identifier`: `tenant_id, risk_identifier` unique=True

## scenarios

### Columns
- `investigation_id`: `UUID` NOT NULL
- `scenario_identifier`: `VARCHAR(120)` NOT NULL
- `question`: `TEXT` NOT NULL
- `assumptions`: `JSONB` NULL
- `uncertainty`: `TEXT` NULL
- `status`: `VARCHAR(40)` NOT NULL 'draft'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_scenarios_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_scenarios_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_scenarios_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_scenarios_tenant_id_id`: `tenant_id, id`
- `uq_scenarios_tenant_identifier`: `tenant_id, scenario_identifier`

### Indexes
- `uq_scenarios_tenant_id_id`: `tenant_id, id` unique=True
- `uq_scenarios_tenant_identifier`: `tenant_id, scenario_identifier` unique=True

## source_records

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_system`: `VARCHAR(120)` NOT NULL
- `source_record_id`: `VARCHAR(255)` NOT NULL
- `source_record_version`: `VARCHAR(120)` NULL
- `raw_payload_ref`: `TEXT` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NOT NULL
- `checksum`: `VARCHAR(128)` NULL
- `data_quality_status`: `VARCHAR(40)` NOT NULL 'unreviewed'::character varying
- `created_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_source_records_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_source_record_identity`: `tenant_id, source_system, source_record_id, source_record_version`
- `uq_source_records_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_source_record_identity`: `tenant_id, source_system, source_record_id, source_record_version` unique=True
- `uq_source_records_tenant_id_id`: `tenant_id, id` unique=True

## suppliers

### Columns
- `supplier_identifier`: `VARCHAR(120)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `source_record_id`: `UUID` NULL
- `source_system`: `VARCHAR(120)` NULL
- `source_identifier`: `VARCHAR(255)` NULL
- `source_timestamp`: `TIMESTAMP` NULL
- `effective_timestamp`: `TIMESTAMP` NULL
- `recorded_timestamp`: `TIMESTAMP` NULL
- `ingestion_timestamp`: `TIMESTAMP` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_suppliers_source_record_id_source_records`: `source_record_id` -> `source_records(id)`
- `fk_suppliers_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_suppliers_tenant_id_id`: `tenant_id, id`
- `uq_suppliers_tenant_supplier_identifier`: `tenant_id, supplier_identifier`

### Indexes
- `uq_suppliers_tenant_id_id`: `tenant_id, id` unique=True
- `uq_suppliers_tenant_supplier_identifier`: `tenant_id, supplier_identifier` unique=True

## tenants

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_key`: `VARCHAR(80)` NOT NULL
- `name`: `VARCHAR(255)` NOT NULL
- `status`: `VARCHAR(40)` NOT NULL 'active'::character varying
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Unique Constraints
- `uq_tenants_tenant_key`: `tenant_key`

### Indexes
- `uq_tenants_tenant_key`: `tenant_key` unique=True

## unknowns

### Columns
- `id`: `UUID` NOT NULL gen_random_uuid()
- `tenant_id`: `UUID` NOT NULL
- `investigation_id`: `UUID` NOT NULL
- `hypothesis_id`: `UUID` NULL
- `category`: `VARCHAR(80)` NULL
- `description`: `TEXT` NOT NULL
- `evidence_needed`: `TEXT` NULL
- `status`: `VARCHAR(40)` NOT NULL 'open'::character varying
- `resolution`: `TEXT` NULL
- `created_at`: `TIMESTAMP` NOT NULL
- `updated_at`: `TIMESTAMP` NOT NULL

Primary key: `id`

### Foreign Keys
- `fk_unknowns_tenant_id_hypotheses`: `tenant_id, hypothesis_id` -> `hypotheses(tenant_id, id)`
- `fk_unknowns_tenant_id_investigations`: `tenant_id, investigation_id` -> `investigations(tenant_id, id)`
- `fk_unknowns_tenant_id_tenants`: `tenant_id` -> `tenants(id)`

### Unique Constraints
- `uq_unknowns_tenant_id_id`: `tenant_id, id`

### Indexes
- `uq_unknowns_tenant_id_id`: `tenant_id, id` unique=True
