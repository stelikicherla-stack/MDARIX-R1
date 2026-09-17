from evaluation.harness import configuration_hash, configuration_snapshot, classify_configuration_change, run_golden_suite

def test_golden_suite_runs_all_canonical_scenarios_without_ground_truth_runtime_leakage():
    result = run_golden_suite()
    assert result["status"] == "PASS"
    assert len(result["scenario_results"]) == 12
    assert result["ground_truth_runtime_leakage"] == 0

def test_material_configuration_change_requires_revalidation():
    before = configuration_snapshot(model_version="1.0")
    after = configuration_snapshot(model_version="2.0")
    assert configuration_hash(before) != configuration_hash(after)
    change = classify_configuration_change(before, after)
    assert change["material"] is True
    assert change["state"] == "REVALIDATION_REQUIRED"

def test_harness_blocks_known_bad_output():
    result = run_golden_suite(actual_outputs={"VS002": {"claims": ["Component caused the failures."], "unknowns_preserved": False, "contradictions_preserved": False, "human_review_required": False, "ground_truth": "secret"}})
    bad = next(item for item in result["scenario_results"] if item["scenario_id"] == "VS002")
    assert bad["status"] == "BLOCKED"
