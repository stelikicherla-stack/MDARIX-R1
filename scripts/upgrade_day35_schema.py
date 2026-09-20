"""Explicitly gated Day 35 schema upgrade command."""
import os
import subprocess
import sys


def main() -> int:
    if os.getenv("DAY35_SCHEMA_APPLY") != "1":
        print("DAY35_SCHEMA_APPLY = DISABLED")
        print("Set DAY35_SCHEMA_APPLY=1 before running Alembic upgrade head.")
        return 2
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
