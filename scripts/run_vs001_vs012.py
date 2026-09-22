"""Run the deterministic VS001-VS012 semantic harness without exposing truth data."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.harness import run_golden_suite


def main() -> int:
    result = run_golden_suite()
    rows = result["scenario_results"]
    out = ROOT / "artifacts" / "stage4-vs001-vs012-results.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["scenario_id", "status"])
        writer.writeheader()
        writer.writerows({"scenario_id": row["scenario_id"], "status": row["status"]} for row in rows)
    print(json.dumps({"status": result["status"], "scenario_count": len(rows), "ground_truth_runtime_leakage": result["ground_truth_runtime_leakage"]}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
