"""Non-mutating validation of the Day 35 Alembic migration chain."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "infrastructure" / "database" / "migrations" / "versions"
EXPECTED = {
    "k27identity_memberships": "j26asksessions",
    "l28roles_permissions": "k27identitymemberships",
    "m29configurations": "l28rolespermissions",
    "n30master_mappings": "m29configurations",
    "o31audit_immutability": "n30mastermappings",
}


def main() -> int:
    for name, parent in EXPECTED.items():
        path = MIGRATIONS / f"{name}.py"
        text = path.read_text(encoding="utf-8")
        revision = re.search(r'^revision\s*=\s*["\']([^"\']+)', text, re.MULTILINE).group(1)
        down_revision = re.search(r'^down_revision\s*=\s*["\']([^"\']+)', text, re.MULTILINE).group(1)
        if revision != name.replace("_", "") and revision != name:
            raise SystemExit(f"Migration revision mismatch: {path}")
        if down_revision != parent:
            raise SystemExit(f"Migration parent mismatch: {path}")
        print(f"PASS | {path.name} | down_revision={down_revision}")
    print("DAY35_MIGRATION_CHAIN = PASS (non-mutating)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
