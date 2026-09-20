from scripts.upgrade_day35_schema import main as upgrade_main
from scripts.verify_day35_database import REQUIRED_TABLES


def test_schema_upgrade_is_gated(monkeypatch):
    monkeypatch.delenv("DAY35_SCHEMA_APPLY", raising=False)
    assert upgrade_main() == 2


def test_required_day35_tables_are_declared():
    assert "tenant_memberships" in REQUIRED_TABLES
    assert "connector_configurations" in REQUIRED_TABLES
