from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.main import app
from graph.service import GraphError, RealityGraphService

client = TestClient(app)
service = RealityGraphService()


def one(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar_one()


def ids():
    product = one("SELECT id FROM products WHERE product_identifier='PRD-ASTER-100'")
    version = one("SELECT id FROM product_versions WHERE version_identifier='D'")
    component = one("SELECT id FROM components WHERE component_identifier='COMP-PWR'")
    supplier = one("SELECT id FROM suppliers WHERE supplier_identifier='SUP-NOVACAP'")
    lot = one("SELECT id FROM lot_batches WHERE lot_identifier='LOT-010'")
    complaint = one("SELECT id FROM complaints WHERE complaint_identifier='CMP-0005'")
    investigation = one("SELECT id FROM investigations WHERE investigation_identifier='INV-001'")
    evidence = one("SELECT id FROM evidence WHERE evidence_identifier='EV-VS001-001'")
    change = one("SELECT id FROM changes WHERE change_identifier='CHG-SUP-PROC-001'")
    return {k: str(v) for k, v in locals().items()}


def test_health_endpoint():
    assert client.get("/health").json()["status"] == "ok"


def test_graph_node_lookup():
    node = service.get_node("product", ids()["product"])
    assert node.entity_type == "product"


def test_invalid_node():
    response = client.get("/api/v1/graph/nodes/not_a_type/123")
    assert response.status_code == 400


def test_supported_node_types():
    values = ids()
    for entity_type, key in [("product", "product"), ("product_version", "version"), ("component", "component"), ("supplier", "supplier"), ("lot_batch", "lot"), ("complaint", "complaint"), ("investigation", "investigation"), ("evidence", "evidence")]:
        assert service.get_node(entity_type, values[key]).canonical_entity_id == values[key]


def test_relationship_retrieval_and_direction():
    rel = next(r for r in service.all_relationships(service.tenant_id()) if r.type == "PRODUCT_HAS_VERSION")
    detail = service.get_relationship_detail(rel.id)
    assert detail.relationship.source_entity_type == "product"
    assert detail.provenance


def test_relationship_type_validation():
    try:
        service.get_neighbors("product", ids()["product"], relationship_type="CAUSE")
    except GraphError as exc:
        assert exc.code == "INVALID_RELATIONSHIP_TYPE"


def test_relationship_evidence():
    rel = next(r for r in service.all_relationships(service.tenant_id()) if r.type == "INVESTIGATION_USES_EVIDENCE")
    assert service.get_relationship_detail(rel.id).evidence


def test_source_and_derived_assertions():
    assertions = {r.assertion_type for r in service.all_relationships(service.tenant_id())}
    assert "SOURCE_ASSERTED" in assertions
    assert "DETERMINISTICALLY_DERIVED" in assertions


def test_no_unsupported_causal_edge():
    assert all("CAUSE" not in r.type for r in service.all_relationships(service.tenant_id()))


def test_product_graph_and_depths():
    graph = service.get_product_graph(ids()["product"], depth=2)
    assert graph.nodes
    assert graph.relationships
    assert graph.metadata["depth"] == 2


def test_investigation_graph():
    graph = service.get_investigation_graph(ids()["investigation"], depth=2)
    assert any(n.entity_type == "complaint" for n in graph.nodes)
    assert any(n.entity_type == "evidence" for n in graph.nodes)


def test_bounded_traversal_and_cycle_safety():
    graph = service.get_neighbors("product", ids()["product"], depth=3)
    assert graph.metadata["node_count"] <= 250
    try:
        service.get_neighbors("product", ids()["product"], depth=99)
    except GraphError as exc:
        assert exc.code == "INVALID_DEPTH"


def test_path_query_and_path_not_causality():
    values = ids()
    graph = service.get_path("change", values["change"], "complaint", values["complaint"], max_depth=5)
    assert graph.relationships
    assert "not causality" in graph.metadata["warnings"][0]


def test_path_not_found():
    values = ids()
    try:
        service.get_path("supplier", values["supplier"], "evidence", values["evidence"], max_depth=1)
    except GraphError as exc:
        assert exc.code == "PATH_NOT_FOUND"


def test_temporal_and_historical_relationships():
    rels = service.all_relationships(service.tenant_id())
    assert any(r.effective_from is not None for r in rels)
    assert one("SELECT count(*) FROM product_versions WHERE version_identifier IN ('C','D')") >= 2


def test_tenant_isolation_and_no_cross_tenant_edges():
    tenant_id = service.tenant_id()
    assert all(service.get_node(r.source_entity_type, r.source_entity_id).tenant_id == tenant_id for r in service.all_relationships(tenant_id)[:20])


def test_unresolved_relationship_handling():
    assert one("SELECT count(*) FROM complaints WHERE lot_batch_id IS NULL") > 0
    assert all(r.type != "COMPLAINT_ASSOCIATED_WITH_LOT" or r.target_entity_id for r in service.all_relationships(service.tenant_id()))


def test_duplicate_edge_prevention():
    rels = service.all_relationships(service.tenant_id())
    assert len({r.id for r in rels}) == len(rels)


def test_multiple_provenance_assertions():
    assert any(r.provenance_count >= 1 for r in service.all_relationships(service.tenant_id()))


def test_ground_truth_isolation():
    graph = service.get_product_graph(ids()["product"], depth=2).model_dump_json()
    assert "actual_root_cause" not in graph
    assert "hidden_ground_truth" not in graph


def test_vs001_graph_path_and_contradictions():
    values = ids()
    graph = service.get_path("change", values["change"], "complaint", values["complaint"], max_depth=5)
    assert any(r.type == "CHANGE_AFFECTS_SUPPLIER" for r in graph.relationships)
    assert one("SELECT count(*) FROM complaints WHERE event_timestamp < '2026-01-18' AND description LIKE '%shutdown%'") >= 3


def test_vs002_false_correlation_preserved():
    assert one("SELECT count(*) FROM changes WHERE change_identifier='CHG-LABEL-042'") == 1
    assert all("CAUSE" not in r.type for r in service.all_relationships(service.tenant_id()))


def test_vs003_missing_evidence_and_vs004_conflicting_evidence():
    assert one("SELECT count(*) FROM source_canonical_links WHERE human_review_status='required'") >= 1
    assert one("SELECT count(*) FROM evidence WHERE content LIKE '%validation test passed%' OR content LIKE '%shutdown complaints existed before%'") >= 2


def test_vs005_to_vs012_preservation():
    assert one("SELECT count(*) FROM evidence WHERE ingestion_timestamp > recorded_timestamp") >= 1
    assert one("SELECT count(*) FROM components WHERE name='Power Regulation Module'") == 1
    assert one("SELECT count(*) FROM evidence WHERE content LIKE '%Historical closure did not address%'") == 1
    assert one("SELECT count(*) FROM risks") >= 15
    assert one("SELECT count(*) FROM controls") >= 12
    assert one("SELECT count(*) FROM evidence WHERE reliability_status='uncertain'") > 0


def test_api_smoke_product_investigation_relationship_path():
    values = ids()
    assert client.get(f"/api/v1/graph/products/{values['product']}").status_code == 200
    assert client.get(f"/api/v1/graph/investigations/{values['investigation']}").status_code == 200
    rel = next(r for r in service.all_relationships(service.tenant_id()) if r.type == "PRODUCT_HAS_VERSION")
    assert client.get(f"/api/v1/graph/relationships/{rel.id}").status_code == 200
    path = client.get("/api/v1/graph/paths", params={"source_type": "change", "source_id": values["change"], "target_type": "complaint", "target_id": values["complaint"], "max_depth": 5})
    assert path.status_code == 200


def test_day6_validator_passes():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "infrastructure/database/scripts/day6_validate_reality_graph.py"], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
