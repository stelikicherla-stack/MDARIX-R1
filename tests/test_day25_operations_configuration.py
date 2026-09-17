import pytest
from backend.app.configuration_lifecycle import ConfigurationLifecycle, ConfigurationVersion
from backend.app.enterprise_audit import safe_details

def test_configuration_requires_ordered_authorized_transitions():
    flow = ConfigurationLifecycle(); draft = ConfigurationVersion("a", "cfg", 1)
    with pytest.raises(ValueError): flow.transition(draft, "ACTIVE", authorized=True, tenant_id="a")
    validated = flow.transition(draft, "VALIDATED", authorized=True, tenant_id="a")
    assert flow.transition(validated, "APPROVED", authorized=True, tenant_id="a").status == "APPROVED"

def test_configuration_denies_tenant_or_authority_spoofing():
    with pytest.raises(PermissionError): ConfigurationLifecycle().transition(ConfigurationVersion("a", "cfg", 1), "VALIDATED", authorized=True, tenant_id="b")
    with pytest.raises(PermissionError): ConfigurationLifecycle().transition(ConfigurationVersion("a", "cfg", 1), "VALIDATED", authorized=False, tenant_id="a")

def test_audit_details_redact_sensitive_keys():
    assert safe_details({"scope":"investigation", "password":"hidden", "authorization_header":"hidden"}) == {"scope":"investigation"}
