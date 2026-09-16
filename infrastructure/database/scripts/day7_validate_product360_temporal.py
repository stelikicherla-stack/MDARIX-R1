import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from backend.app.db.session import engine  # noqa: E402
from backend.app.product360.service import Product360Service  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"DAY 7 PRODUCT 360 / TEMPORAL VALIDATION = FAIL\n{message}")


def main() -> int:
    service = Product360Service()
    products = service.list_products()
    if len(products) < 2:
        fail("Expected at least two products.")
    primary = next((p for p in products if p.product_identifier == "PRD-ASTER-100"), None)
    if not primary:
        fail("Primary AsterFlow product missing.")
    view = service.product360(primary.id, version_id="D")
    if not view.selected_version or view.selected_version["version_identifier"] != "D":
        fail("Rev D Product 360 view unavailable.")
    if view.overview["component_count"] < 4:
        fail("Configuration components missing.")
    if view.overview["complaint_count"] < 1:
        fail("Complaint context missing.")
    if not view.evidence:
        fail("Evidence context missing.")
    if not view.limitations:
        fail("Data-quality limitations missing.")
    if any("root cause" in str(item).lower() for item in [view.overview, view.limitations]):
        if not any("no root-cause conclusion" in item["description"].lower() for item in view.limitations):
            fail("Unsupported root-cause wording detected.")
    event_as_of = service.temporal_reality(primary.id, version_id="D", as_of=datetime(2026, 2, 15, tzinfo=timezone.utc), mode="event")
    known_as_of = service.temporal_reality(primary.id, version_id="D", as_of=datetime(2026, 2, 15, tzinfo=timezone.utc), mode="known")
    if event_as_of.event_count < known_as_of.event_count:
        fail("Event-as-of should not be narrower than known-as-of for the same date.")
    if not any(event.late_arriving for event in service.temporal_reality(primary.id, version_id="D").events):
        fail("Late-arriving evidence not represented.")
    payload = view.model_dump_json()
    for forbidden in ["hidden_ground_truth", "actual_root_cause", "correct_answer", "expected_conclusion", "prohibited_conclusions"]:
        if forbidden in payload:
            fail(f"Ground Truth leakage detected: {forbidden}")
    with engine.connect() as conn:
        # Verify all Day 7 canonical products share exactly one tenant (the ACME_CARE_SYNTHETIC tenant)
        day7_tenant_count = conn.execute(
            text("""
                SELECT count(distinct tenant_id) FROM products
                WHERE product_identifier IN ('PRD-ASTER-100', 'PRD-LEGACY-001', 'PRD-MK2-200')
            """)
        ).scalar_one()
    if day7_tenant_count != 1:
        fail("Unexpected tenant count for Day 7 validation: Day 7 canonical products do not share a single tenant.")
    print("DAY 7 PRODUCT 360 / TEMPORAL VALIDATION = PASS")
    print(f"products={len(products)}")
    print(f"timeline_events={len(view.timeline)}")
    print(f"event_as_of={event_as_of.event_count}")
    print(f"known_as_of={known_as_of.event_count}")
    print("ground_truth_leakage=0")
    print("unsupported_causal_conclusions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
