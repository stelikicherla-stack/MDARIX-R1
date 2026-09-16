from datetime import datetime, timezone

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from backend.app.db.session import engine


NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
EFFECTIVE = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc)


@pytest.fixture()
def conn():
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


def scalar(conn, sql, **params):
    return conn.execute(text(sql), params).scalar_one()


def seed_core(conn):
    tenant = scalar(conn, "INSERT INTO tenants (tenant_key, name, created_at, updated_at) VALUES ('t-a', 'Tenant A', :n, :n) RETURNING id", n=NOW)
    product = scalar(conn, "INSERT INTO products (tenant_id, product_identifier, name, lifecycle_status, created_at, updated_at) VALUES (:t, 'P-100', 'Infusion Pump', 'active', :n, :n) RETURNING id", t=tenant, n=NOW)
    version = scalar(conn, "INSERT INTO product_versions (tenant_id, product_id, version_identifier, lifecycle_status, release_timestamp, created_at, updated_at) VALUES (:t, :p, 'Rev D', 'active', :e, :n, :n) RETURNING id", t=tenant, p=product, e=EFFECTIVE, n=NOW)
    component = scalar(conn, "INSERT INTO components (tenant_id, component_identifier, name, revision, created_at, updated_at) VALUES (:t, 'C-200', 'Power Module', 'Rev B', :n, :n) RETURNING id", t=tenant, n=NOW)
    supplier = scalar(conn, "INSERT INTO suppliers (tenant_id, supplier_identifier, name, created_at, updated_at) VALUES (:t, 'S-300', 'Supplier One', :n, :n) RETURNING id", t=tenant, n=NOW)
    site = scalar(conn, "INSERT INTO manufacturing_sites (tenant_id, site_identifier, name, created_at, updated_at) VALUES (:t, 'M-1', 'Site One', :n, :n) RETURNING id", t=tenant, n=NOW)
    lot = scalar(conn, "INSERT INTO lot_batches (tenant_id, lot_identifier, product_version_id, manufacturing_site_id, created_at, updated_at) VALUES (:t, 'L-400', :v, :s, :n, :n) RETURNING id", t=tenant, v=version, s=site, n=NOW)
    complaint = scalar(conn, "INSERT INTO complaints (tenant_id, complaint_identifier, product_id, product_version_id, lot_batch_id, event_timestamp, complaint_timestamp, description, created_at, updated_at) VALUES (:t, 'CPL-1', :p, :v, :l, :e, :n, 'Intermittent shutdown', :n, :n) RETURNING id", t=tenant, p=product, v=version, l=lot, e=EFFECTIVE, n=NOW)
    investigation = scalar(conn, "INSERT INTO investigations (tenant_id, investigation_identifier, product_id, investigation_question, opened_at, created_at, updated_at) VALUES (:t, 'INV-1', :p, 'Why did shutdown complaints increase after Rev D?', :n, :n, :n) RETURNING id", t=tenant, p=product, n=NOW)
    evidence_support = scalar(conn, "INSERT INTO evidence (tenant_id, evidence_identifier, investigation_id, evidence_type, title, reliability_status, fact_type, content, created_at, updated_at) VALUES (:t, 'EV-1', :i, 'complaint_summary', 'Complaint increase after Rev B', 'reviewed', 'source_fact', 'Frequency increased after Rev B introduction', :n, :n) RETURNING id", t=tenant, i=investigation, n=NOW)
    evidence_contra = scalar(conn, "INSERT INTO evidence (tenant_id, evidence_identifier, investigation_id, evidence_type, title, reliability_status, fact_type, content, created_at, updated_at) VALUES (:t, 'EV-2', :i, 'complaint_history', 'Pre-Rev B shutdown complaints', 'reviewed', 'source_fact', 'Three shutdown complaints existed before Rev B', :n, :n) RETURNING id", t=tenant, i=investigation, n=NOW)
    hypothesis = scalar(conn, "INSERT INTO hypotheses (tenant_id, investigation_id, statement, origin, created_at, updated_at) VALUES (:t, :i, 'Component Rev B may have contributed to shutdown complaints.', 'ai', :n, :n) RETURNING id", t=tenant, i=investigation, n=NOW)
    return {
        "tenant": tenant,
        "product": product,
        "version": version,
        "component": component,
        "supplier": supplier,
        "site": site,
        "lot": lot,
        "complaint": complaint,
        "investigation": investigation,
        "evidence_support": evidence_support,
        "evidence_contra": evidence_contra,
        "hypothesis": hypothesis,
    }


def test_database_connection_and_version(conn):
    assert scalar(conn, "SELECT current_database()") == "mdarix_r1"
    assert scalar(conn, "SELECT current_setting('server_version')").startswith("16.")


def test_pgvector_enabled(conn):
    assert scalar(conn, "SELECT extversion FROM pg_extension WHERE extname='vector'")


def test_core_tables_exist(conn):
    tables = set(inspect(conn).get_table_names())
    for name in [
        "tenants", "source_records", "products", "product_versions", "components", "suppliers",
        "manufacturing_sites", "lot_batches", "requirements", "changes", "complaints",
        "investigations", "risks", "failure_modes", "controls", "evidence", "hypotheses",
        "unknowns", "failure_chains", "failure_chain_nodes", "failure_chain_edges", "scenarios",
        "decisions", "ai_executions", "human_reviews", "reality_relationships", "evidence_embeddings",
    ]:
        assert name in tables


def test_required_foreign_keys_and_unique_constraints_exist(conn):
    inspector = inspect(conn)
    assert inspector.get_foreign_keys("product_versions")
    assert any(c["name"] == "uq_products_tenant_product_identifier" for c in inspector.get_unique_constraints("products"))


def test_tenant_product_version_component_supplier_lot_relationships(conn):
    ids = seed_core(conn)
    scalar(conn, "INSERT INTO product_components (tenant_id, product_version_id, component_id, created_at) VALUES (:t, :v, :c, :n) RETURNING id", t=ids["tenant"], v=ids["version"], c=ids["component"], n=NOW)
    scalar(conn, "INSERT INTO component_suppliers (tenant_id, component_id, supplier_id, created_at) VALUES (:t, :c, :s, :n) RETURNING id", t=ids["tenant"], c=ids["component"], s=ids["supplier"], n=NOW)
    scalar(conn, "INSERT INTO lot_components (tenant_id, lot_batch_id, component_id, created_at) VALUES (:t, :l, :c, :n) RETURNING id", t=ids["tenant"], l=ids["lot"], c=ids["component"], n=NOW)


def test_complaint_and_investigation_relationships(conn):
    ids = seed_core(conn)
    scalar(conn, "INSERT INTO investigation_complaints (tenant_id, investigation_id, complaint_id, created_at) VALUES (:t, :i, :c, :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], c=ids["complaint"], n=NOW)
    scalar(conn, "INSERT INTO investigation_evidence (tenant_id, investigation_id, evidence_id, created_at) VALUES (:t, :i, :e, :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], e=ids["evidence_support"], n=NOW)


def test_multiple_hypotheses_per_investigation(conn):
    ids = seed_core(conn)
    scalar(conn, "INSERT INTO hypotheses (tenant_id, investigation_id, statement, origin, created_at, updated_at) VALUES (:t, :i, 'Alternative cause remains possible.', 'human', :n, :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], n=NOW)
    assert scalar(conn, "SELECT count(*) FROM hypotheses WHERE investigation_id=:i", i=ids["investigation"]) == 2


def test_evidence_support_and_contradict_relationships(conn):
    ids = seed_core(conn)
    scalar(conn, "INSERT INTO hypothesis_evidence (tenant_id, hypothesis_id, evidence_id, relation_type, rationale, created_by_type, created_at) VALUES (:t, :h, :e, 'support', 'Temporal increase observed', 'system', :n) RETURNING id", t=ids["tenant"], h=ids["hypothesis"], e=ids["evidence_support"], n=NOW)
    scalar(conn, "INSERT INTO hypothesis_evidence (tenant_id, hypothesis_id, evidence_id, relation_type, rationale, created_by_type, created_at) VALUES (:t, :h, :e, 'contradict', 'Complaints existed before Rev B', 'system', :n) RETURNING id", t=ids["tenant"], h=ids["hypothesis"], e=ids["evidence_contra"], n=NOW)
    assert scalar(conn, "SELECT count(distinct relation_type) FROM hypothesis_evidence WHERE hypothesis_id=:h", h=ids["hypothesis"]) == 2


def test_unknown_is_explicit_not_null(conn):
    ids = seed_core(conn)
    unknown = scalar(conn, "INSERT INTO unknowns (tenant_id, investigation_id, hypothesis_id, category, description, evidence_needed, created_at, updated_at) VALUES (:t, :i, :h, 'missing_testing', 'Comparative Rev A vs Rev B testing unavailable', 'Comparative test report', :n, :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], h=ids["hypothesis"], n=NOW)
    assert unknown


def test_failure_chain_nodes_edges_persist_hypothesized(conn):
    ids = seed_core(conn)
    chain = scalar(conn, "INSERT INTO failure_chains (tenant_id, investigation_id, name, created_at, updated_at) VALUES (:t, :i, 'Shutdown failure chain', :n, :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], n=NOW)
    n1 = scalar(conn, "INSERT INTO failure_chain_nodes (tenant_id, failure_chain_id, sequence_number, node_type, label, created_at) VALUES (:t, :f, 1, 'change', 'Supplier Process Change', :n) RETURNING id", t=ids["tenant"], f=chain, n=NOW)
    n2 = scalar(conn, "INSERT INTO failure_chain_nodes (tenant_id, failure_chain_id, sequence_number, node_type, label, created_at) VALUES (:t, :f, 2, 'component', 'Component Rev B', :n) RETURNING id", t=ids["tenant"], f=chain, n=NOW)
    edge = scalar(conn, "INSERT INTO failure_chain_edges (tenant_id, failure_chain_id, from_node_id, to_node_id, edge_status, created_at) VALUES (:t, :f, :a, :b, 'hypothesized', :n) RETURNING id", t=ids["tenant"], f=chain, a=n1, b=n2, n=NOW)
    assert edge


def test_ai_execution_human_review_and_decision_are_distinct(conn):
    ids = seed_core(conn)
    ai = scalar(conn, "INSERT INTO ai_executions (tenant_id, investigation_id, provider, model_name, structured_output, rationale_summary, execution_timestamp) VALUES (:t, :i, 'openai-compatible', 'test-model', '{\"finding\":\"draft\"}', 'Evidence-grounded summary only', :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], n=NOW)
    decision = scalar(conn, "INSERT INTO decisions (tenant_id, investigation_id, decision_identifier, decision_type, disposition, rationale, decision_timestamp, authorized_by_ref, created_at) VALUES (:t, :i, 'DEC-1', 'investigation_disposition', 'continue_investigation', 'Causality not established', :n, 'reviewer-1', :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], n=NOW)
    review = scalar(conn, "INSERT INTO human_reviews (tenant_id, investigation_id, ai_execution_id, decision_id, reviewer_ref, disposition, review_timestamp) VALUES (:t, :i, :a, :d, 'reviewer-1', 'approved_with_limits', :n) RETURNING id", t=ids["tenant"], i=ids["investigation"], a=ai, d=decision, n=NOW)
    assert ai != decision
    assert review


def test_ai_execution_has_no_chain_of_thought_column(conn):
    columns = {c["name"] for c in inspect(conn).get_columns("ai_executions")}
    assert "chain_of_thought" not in columns


def test_temporal_fields_preserve_distinct_meanings(conn):
    ids = seed_core(conn)
    source = scalar(conn, "INSERT INTO source_records (tenant_id, source_system, source_record_id, source_timestamp, effective_timestamp, ingestion_timestamp, created_at) VALUES (:t, 'PLM', 'SRC-1', :e, :e, :n, :n) RETURNING id", t=ids["tenant"], e=EFFECTIVE, n=NOW)
    assert source
    row = conn.execute(text("SELECT effective_timestamp, ingestion_timestamp FROM source_records WHERE id=:id"), {"id": source}).one()
    assert row.effective_timestamp != row.ingestion_timestamp
    assert row.effective_timestamp.tzinfo is not None


def test_source_fact_and_hypothesis_are_separate(conn):
    ids = seed_core(conn)
    assert scalar(conn, "SELECT fact_type FROM evidence WHERE id=:e", e=ids["evidence_support"]) == "source_fact"
    assert scalar(conn, "SELECT statement FROM hypotheses WHERE id=:h", h=ids["hypothesis"]).startswith("Component Rev B may")


def test_cross_tenant_relationship_is_prevented(conn):
    ids = seed_core(conn)
    tenant_b = scalar(conn, "INSERT INTO tenants (tenant_key, name, created_at, updated_at) VALUES ('t-b', 'Tenant B', :n, :n) RETURNING id", n=NOW)
    with pytest.raises(DBAPIError):
        conn.execute(text("INSERT INTO product_versions (tenant_id, product_id, version_identifier, created_at, updated_at) VALUES (:tb, :pa, 'Bad', :n, :n)"), {"tb": tenant_b, "pa": ids["product"], "n": NOW})


def test_vector_foundation_column_exists(conn):
    result = scalar(conn, "SELECT udt_name FROM information_schema.columns WHERE table_name='evidence_embeddings' AND column_name='embedding'")
    assert result == "vector"


def test_alembic_at_head(conn):
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    current = scalar(conn, "SELECT version_num FROM alembic_version")
    assert current == head
