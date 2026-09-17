import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "evaluation" / "fixtures" / "VS009_counterfactual_fixture.json"


def test_vs009_fixture_is_canonical_nimbus_identity():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["scenario_id"] == "VS009"
    assert fixture["product_identifier"] == "PRD-NIMBUS-200"
    assert fixture["investigation_identifier"] == "INV-009"
    assert fixture["intervention_target"] == "CHG-GEN-006"
    assert "Component Rev B" not in fixture["intervention_description"]


def test_vs009_fixture_preserves_counterfactual_boundaries():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["invariants"]
    assert fixture["expected_affected_relationships"]
    assert fixture["expected_unknowns"]
    assert all("caused" not in claim.lower() or "definitely" in claim.lower() for claim in fixture["prohibited_conclusions"])


def test_golden_builder_is_idempotent():
    script = "import hashlib,json; from data.golden.generators.generate_r1_golden_dataset import build_dataset; print(hashlib.sha256(json.dumps(build_dataset(),sort_keys=True,default=str).encode()).hexdigest()); print(hashlib.sha256(json.dumps(build_dataset(),sort_keys=True,default=str).encode()).hexdigest())"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    output = subprocess.check_output([sys.executable, "-c", script], env=env, text=True).splitlines()
    first, second = output[-2:]
    assert first == second
