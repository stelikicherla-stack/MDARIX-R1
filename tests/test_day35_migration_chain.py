from scripts.validate_day35_migrations import EXPECTED, MIGRATIONS


def test_day35_migration_chain_is_contiguous():
    import re
    for name, parent in EXPECTED.items():
        text = (MIGRATIONS / f"{name}.py").read_text(encoding="utf-8")
        assert re.search(rf'^down_revision\s*=\s*["\']{parent}["\']', text, re.MULTILINE)
