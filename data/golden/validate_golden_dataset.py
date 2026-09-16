import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "golden"
CANONICAL_PATH = BASE / "canonical" / "r1_canonical_golden_dataset.json"
MANIFEST_PATH = BASE / "GOLDEN_DATASET_MANIFEST.json"
GROUND = ROOT / "evaluation" / "ground_truth"
NOTICE = "MDARIX R1 GOLDEN DATASET - SYNTHETIC TEST DATA ONLY. NOT FOR CLINICAL OR REGULATORY USE."
FORBIDDEN_APP_KEYS = {
    "hidden_ground_truth",
    "correct_answer",
    "actual_root_cause",
    "expected_conclusion",
    "prohibited_conclusions",
    "expected_system_behavior",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def ids_unique(records: list[dict], key: str) -> bool:
    values = [record[key] for record in records]
    return len(values) == len(set(values))


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    data = load_json(CANONICAL_PATH)
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

    if manifest["notice"] != NOTICE or data["notice"] != NOTICE:
        fail("Synthetic-only notice missing")
    if manifest["canonical_sha256"] != digest:
        fail("Manifest hash does not match canonical dataset")

    counts = manifest["counts"]
    expected = {
        "product_families": 2,
        "products": 2,
        "suppliers": 5,
        "manufacturing_sites": 2,
        "investigations": 10,
        "scenarios": 12,
    }
    for key, expected_value in expected.items():
        if counts[key] != expected_value:
            fail(f"Unexpected {key} count")
    if not (15 <= counts["components"] <= 20):
        fail("Component count outside target range")
    if not (15 <= counts["lots"] <= 20):
        fail("Lot count outside target range")
    if not (15 <= counts["changes"] <= 20):
        fail("Change count outside target range")
    if not (100 <= counts["complaints"] <= 150):
        fail("Complaint count outside target range")
    if not (30 <= counts["evidence"] <= 50):
        fail("Evidence count outside target range")

    for records, key in [
        (data["product_versions"], "product_version_id"),
        (data["components"], "component_id"),
        (data["lots"], "lot_id"),
        (data["complaints"], "complaint_id"),
        (data["investigations"], "investigation_id"),
        (data["evidence"], "evidence_id"),
    ]:
        if not ids_unique(records, key):
            fail(f"Duplicate IDs for {key}")

    version_ids = {item["product_version_id"] for item in data["product_versions"]}
    lot_ids = {item["lot_id"] for item in data["lots"]}
    investigation_ids = {item["investigation_id"] for item in data["investigations"]}
    if any(item["product_version_id"] not in version_ids for item in data["complaints"]):
        fail("Complaint references unknown product version")
    if any(item["lot_id"] is not None and item["lot_id"] not in lot_ids for item in data["complaints"]):
        fail("Complaint references unknown lot")
    if any(item["investigation_id"] not in investigation_ids for item in data["evidence"]):
        fail("Evidence references unknown investigation")

    scenario_ids = {item["scenario_id"] for item in data["scenarios"]}
    if scenario_ids != {f"VS{i:03d}" for i in range(1, 13)}:
        fail("Scenario IDs VS001-VS012 are not complete")

    pre_rev_b_shutdown = [
        c for c in data["complaints"]
        if c["failure_mode"] == "shutdown" and c["event_timestamp"] < "2026-01-18"
    ]
    if len(pre_rev_b_shutdown) < 3:
        fail("VS001 contradiction missing: pre-Rev B shutdown complaints")
    evidence_titles = {item["title"] for item in data["evidence"]}
    if "Rev B qualification passed" not in evidence_titles:
        fail("VS001 contradiction missing: Rev B validation passed")
    if not any(lot["traceability_status"] == "incomplete" for lot in data["lots"]):
        fail("Incomplete lot traceability missing")
    if not any("Comparative Rev A versus Rev B" in u["description"] for u in data["unknowns"]):
        fail("Explicit comparative testing unknown missing")

    anomaly_types = {item["type"] for item in data["intentional_anomalies"]}
    for required in ["identity_variation", "false_correlation", "multiple_causes", "late_arriving_evidence", "duplicate_candidate"]:
        if required not in anomaly_types:
            fail(f"Missing anomaly type {required}")

    if FORBIDDEN_APP_KEYS & set(walk_keys(data)):
        fail("Ground Truth/evaluation keys leaked into application-facing canonical data")
    for path in BASE.rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".json", ".csv", ".md", ".py"}:
            fail(f"Unexpected file type in golden data: {path}")
        if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md"}:
            text = path.read_text(encoding="utf-8")
            if any(marker in text.lower() for marker in ["patient name", "ssn", "date of birth", "real customer"]):
                fail(f"PII marker found in {path}")

    for sid in scenario_ids:
        if not (GROUND / sid / "ground_truth.json").exists():
            fail(f"Missing ground truth for {sid}")

    print("GOLDEN DATASET VALIDATION = PASS")
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"GOLDEN DATASET VALIDATION = FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
