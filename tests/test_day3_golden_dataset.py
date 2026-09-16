import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "golden" / "canonical" / "r1_canonical_golden_dataset.json"
MANIFEST = ROOT / "data" / "golden" / "GOLDEN_DATASET_MANIFEST.json"
GROUND = ROOT / "evaluation" / "ground_truth"
FORBIDDEN_APP_KEYS = {"hidden_ground_truth", "correct_answer", "actual_root_cause", "expected_conclusion", "prohibited_conclusions"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def test_expected_record_counts():
    counts = load(MANIFEST)["counts"]
    assert counts["product_families"] == 2
    assert counts["products"] == 2
    assert counts["product_versions"] >= 4
    assert 15 <= counts["components"] <= 20
    assert counts["suppliers"] == 5
    assert counts["manufacturing_sites"] == 2
    assert 15 <= counts["lots"] <= 20
    assert 15 <= counts["changes"] <= 20
    assert 100 <= counts["complaints"] <= 150
    assert counts["investigations"] == 10
    assert counts["risks"] == 15
    assert counts["failure_modes"] == 15
    assert 30 <= counts["evidence"] <= 50


def test_unique_ids_and_relationships():
    data = load(CANONICAL)
    for collection, key in [("complaints", "complaint_id"), ("evidence", "evidence_id"), ("investigations", "investigation_id")]:
        values = [row[key] for row in data[collection]]
        assert len(values) == len(set(values))
    version_ids = {row["product_version_id"] for row in data["product_versions"]}
    lot_ids = {row["lot_id"] for row in data["lots"]}
    assert all(row["product_version_id"] in version_ids for row in data["complaints"])
    assert all(row["lot_id"] is None or row["lot_id"] in lot_ids for row in data["complaints"])


def test_all_12_scenarios_exist():
    data = load(CANONICAL)
    assert {s["scenario_id"] for s in data["scenarios"]} == {f"VS{i:03d}" for i in range(1, 13)}
    for sid in [f"VS{i:03d}" for i in range(1, 13)]:
        assert (GROUND / sid / "ground_truth.json").exists()


def test_primary_scenario_required_contradictions_and_unknowns():
    data = load(CANONICAL)
    pre_rev_b = [c for c in data["complaints"] if c["failure_mode"] == "shutdown" and c["event_timestamp"] < "2026-01-18"]
    assert len(pre_rev_b) >= 3
    assert any(e["title"] == "Rev B qualification passed" for e in data["evidence"])
    assert any(l["traceability_status"] == "incomplete" for l in data["lots"])
    assert any("Comparative Rev A versus Rev B" in u["description"] for u in data["unknowns"])


def test_false_correlation_multiple_cause_abstention_and_shared_component_exist():
    data = load(CANONICAL)
    anomaly_types = {a["type"] for a in data["intentional_anomalies"]}
    assert "false_correlation" in anomaly_types
    assert "multiple_causes" in anomaly_types
    assert any("Field operating condition not recorded" in u["description"] for u in data["unknowns"])
    assert any(c["component_id"] == "COMP-PWR" for c in data["components"])


def test_temporal_integrity_and_late_arriving_information():
    data = load(CANONICAL)
    assert all(c["event_timestamp"] <= c["recorded_timestamp"] <= c["ingestion_timestamp"] for c in data["complaints"])
    late = [e for e in data["evidence"] if e["evidence_id"] == "EV-VS001-003"][0]
    assert late["ingestion_timestamp"] > "2026-04-01"


def test_ground_truth_isolation_and_leakage():
    data = load(CANONICAL)
    assert not (FORBIDDEN_APP_KEYS & set(walk_keys(data)))
    gt = load(GROUND / "VS001" / "ground_truth.json")
    assert gt["evaluation_only"] is True
    assert "hidden_ground_truth" in gt


def test_deterministic_generation_hash_matches_manifest():
    data = load(CANONICAL)
    manifest = load(MANIFEST)
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
    assert digest == manifest["canonical_sha256"]


def test_generator_is_repeatable():
    before = load(MANIFEST)["canonical_sha256"]
    result = subprocess.run([sys.executable, "data/golden/generators/generate_r1_golden_dataset.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    after = load(MANIFEST)["canonical_sha256"]
    assert after == before


def test_validator_passes():
    result = subprocess.run([sys.executable, "data/golden/validate_golden_dataset.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_pii_or_secret_markers():
    for path in (ROOT / "data" / "golden").rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md"}:
            text = path.read_text(encoding="utf-8").lower()
            assert "gho_" not in text
            assert "patient name" not in text
            assert "date of birth" not in text
            assert "ssn" not in text
