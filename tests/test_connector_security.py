import os

import pytest

from access_control.configuration_safety import safe_configuration
from backend.app.access_router import _safe_provider_url


def test_managed_secret_reference_is_allowed_but_secret_values_are_not_persistable():
    assert safe_configuration({"credential_ref": "TRACKWISE_TOKEN", "endpoint": "https://provider.example"})["credential_ref"] == "TRACKWISE_TOKEN"
    with pytest.raises(ValueError):
        safe_configuration({"api_token": "secret-value"})
    with pytest.raises(ValueError):
        safe_configuration({"credential_ref": "bad ref"})


def test_provider_urls_strip_fragments_and_reject_private_destinations_in_production(monkeypatch):
    monkeypatch.setenv("MDARIX_ENV", "production")
    with pytest.raises(ValueError, match="PRIVATE_DESTINATION"):
        _safe_provider_url("http://127.0.0.1:8101", "health")
    assert _safe_provider_url("https://93.184.216.34/base", "/schema", timeout=5) == "https://93.184.216.34/schema"
    monkeypatch.setenv("MDARIX_ENV", "development")
    assert _safe_provider_url("http://127.0.0.1:8101", "health") == "http://127.0.0.1:8101/health"
