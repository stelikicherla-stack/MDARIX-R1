from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.main import app
from backend.app.product360.service import Product360Service

client = TestClient(app)
service = Product360Service()


def scalar(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar_one()


def primary_product():
    return scalar("SELECT id FROM products WHERE product_identifier='PRD-ASTER-100'")


def test_product_list_operational():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert any(item["product_identifier"] == "PRD-ASTER-100" for item in response.json())


def test_product360_header_and_version_selector():
    product_id = str(primary_product())
    response = client.get(f"/api/v1/products/{product_id}/product-360", params={"version_id": "D"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["product"]["name"] == "AsterFlow 100 Controller"
    assert payload["selected_version"]["version_identifier"] == "D"
    assert len(payload["versions"]) >= 4


def test_configuration_component_supplier_context():
    view = service.product360(str(primary_product()), version_id="D")
    assert any(c["component_identifier"] == "COMP-PWR" for c in view.configuration["components"])
    assert any("NovaCap" in s["name"] for s in view.configuration["suppliers"])


def test_configuration_components_are_relationship_derived():
    view = service.product360(str(primary_product()), version_id="D")
    component_ids = {c["id"] for c in view.configuration["components"]}
    expected_ids = {
        str(row[0])
        for row in engine.connect().execute(
            text(
                "SELECT component_id FROM product_components pc "
                "JOIN product_versions pv ON pv.tenant_id=pc.tenant_id AND pv.id=pc.product_version_id "
                "WHERE pv.version_identifier='D'"
            )
        )
    }
    assert component_ids == expected_ids


def test_change_manufacturing_lot_context():
    view = service.product360(str(primary_product()), version_id="D")
    assert any(c["change_identifier"] == "CHG-SUP-PROC-001" for c in view.changes)
    assert any(lot["traceability_state"] == "PARTIAL" for lot in view.manufacturing["lots"])


def test_complaint_investigation_context():
    view = service.product360(str(primary_product()), version_id="D")
    assert view.complaints
    assert any("shutdown" in c["description"] for c in view.complaints)
    assert any(i["investigation_identifier"] == "INV-001" for i in view.investigations)


def test_product_investigation_access_preserves_association_outside_historical_snapshot():
    product_id = str(primary_product())
    response = client.get(f"/api/v1/products/{product_id}/investigations")
    assert response.status_code == 200
    payload = response.json()
    assert [item["investigation_identifier"] for item in payload] == [f"INV-{number:03d}" for number in range(1, 8)]
    assert len({item["id"] for item in payload}) == 7

    historical = service.product360(product_id, version_id="D", as_of=datetime(2026, 2, 15, tzinfo=timezone.utc), mode="event")
    assert historical.investigations == []


def test_risk_failure_mode_control_evidence_context():
    view = service.product360(str(primary_product()), version_id="D")
    assert view.risks
    assert view.failure_modes
    assert view.controls
    assert view.evidence


def test_provenance_and_limitations_visible():
    view = service.product360(str(primary_product()), version_id="D")
    assert view.provenance
    assert any(item["code"] == "INCOMPLETE_TRACEABILITY" for item in view.limitations)
    assert any(item["code"] == "NO_CAUSAL_CONCLUSION" for item in view.limitations)


def test_timeline_temporal_dimensions():
    view = service.product360(str(primary_product()), version_id="D")
    complaint = next(e for e in view.timeline if e.event_type == "COMPLAINT_EVENT")
    assert complaint.event_time
    assert complaint.recorded_time
    assert complaint.knowledge_available_time


def test_as_of_known_vs_event():
    product_id = str(primary_product())
    as_of = datetime(2026, 2, 15, tzinfo=timezone.utc)
    event_view = service.temporal_reality(product_id, version_id="D", as_of=as_of, mode="event")
    known_view = service.temporal_reality(product_id, version_id="D", as_of=as_of, mode="known")
    assert event_view.event_count >= known_view.event_count


def test_product360_known_as_of_filters_section_payloads():
    product_id = str(primary_product())
    as_of = datetime(2026, 2, 15, tzinfo=timezone.utc)
    view = service.product360(product_id, version_id="D", as_of=as_of, mode="known")
    assert all(datetime.fromisoformat(c["ingestion_timestamp"]) <= as_of for c in view.complaints)
    assert all(datetime.fromisoformat(e["ingestion_timestamp"]) <= as_of for e in view.evidence)
    assert view.overview["complaint_count"] == len(view.complaints)
    assert view.overview["evidence_count"] == len(view.evidence)


def test_product360_event_as_of_does_not_show_future_effective_sections():
    product_id = str(primary_product())
    as_of = datetime(2026, 1, 16, tzinfo=timezone.utc)
    view = service.product360(product_id, version_id="D", as_of=as_of, mode="event")
    assert all(datetime.fromisoformat(c["effective_timestamp"]) <= as_of for c in view.changes if c["effective_timestamp"])
    assert all(datetime.fromisoformat(l["manufactured_timestamp"]) <= as_of for l in view.manufacturing["lots"])


def test_late_arriving_evidence_visible():
    timeline = service.temporal_reality(str(primary_product()), version_id="D")
    assert any(event.late_arriving for event in timeline.events)


def test_historical_rev_c_vs_rev_d():
    product_id = str(primary_product())
    rev_c = service.product360(product_id, version_id="C")
    rev_d = service.product360(product_id, version_id="D")
    assert rev_c.selected_version["version_identifier"] == "C"
    assert rev_d.selected_version["version_identifier"] == "D"


def test_timeline_filter_category_and_date_range():
    view = service.product360(str(primary_product()), version_id="D")
    categories = {event.category for event in view.timeline}
    assert {"DESIGN", "FIELD", "EVIDENCE"}.issubset(categories)


def test_vs001_end_to_end_no_root_cause():
    view = service.product360(str(primary_product()), version_id="D")
    payload = view.model_dump_json().lower()
    assert "component/supplier change is the leading hypothesis" not in payload
    assert "no root-cause conclusion" in payload


def test_vs005_and_vs007_temporal_preservation():
    view = service.product360(str(primary_product()), version_id="D")
    assert any(event.late_arriving for event in view.timeline)
    assert scalar("SELECT count(*) FROM evidence WHERE content LIKE '%Historical closure did not address%'") == 1


def test_ground_truth_and_tenant_isolation():
    view = service.product360(str(primary_product()), version_id="D")
    payload = view.model_dump_json()
    assert "actual_root_cause" not in payload
    # Verify all Day 7 canonical products share exactly one tenant
    # (Using scoped query to remain robust as subsequent days add test data)
    assert scalar(
        "SELECT count(distinct tenant_id) FROM products "
        "WHERE product_identifier IN ('PRD-ASTER-100', 'PRD-LEGACY-001', 'PRD-MK2-200')"
    ) == 1


def test_api_timeline_endpoint():
    response = client.get(f"/api/v1/products/{primary_product()}/timeline", params={"version_id": "D", "mode": "known", "as_of": "2026-02-15T00:00:00Z"})
    assert response.status_code == 200
    assert response.json()["mode"] == "known"


def test_day7_validator_passes():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "infrastructure/database/scripts/day7_validate_product360_temporal.py"], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
