"""Validate/export the deterministic Day 35 identity fixture.

This command is non-mutating by default. Database provisioning requires the
explicit DAY35_FIXTURE_APPLY=1 gate and is intentionally left to the operator.
"""
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from access_control.fixtures import FIXTURE_TENANTS, FIXTURE_USERS, validate_fixture


def main() -> int:
    validate_fixture()
    payload = {
        "tenants": [asdict(item) for item in FIXTURE_TENANTS],
        "users": [asdict(item) for item in FIXTURE_USERS],
        "database_apply_enabled": os.getenv("DAY35_FIXTURE_APPLY") == "1",
    }
    output = Path(os.getenv("DAY35_FIXTURE_OUTPUT", "artifacts/day35-identity-fixture.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"DAY35_FIXTURE_VALID = PASS ({len(FIXTURE_TENANTS)} tenants, {len(FIXTURE_USERS)} users)")
    print(f"DAY35_FIXTURE_OUTPUT = {output}")
    if not payload["database_apply_enabled"]:
        print("DAY35_FIXTURE_DATABASE_APPLY = DISABLED (non-mutating mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
