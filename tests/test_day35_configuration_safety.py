import pytest

from access_control.configuration_safety import safe_configuration


def test_configuration_safety_accepts_non_secret_metadata():
    assert safe_configuration({"endpoint": "https://example.invalid", "timeout_seconds": 30})["timeout_seconds"] == 30


@pytest.mark.parametrize("key", ["password", "api_token", "client_secret", "private_key", "cookie"])
def test_configuration_safety_rejects_sensitive_values(key):
    with pytest.raises(ValueError, match="SENSITIVE_CONFIGURATION_FIELD"):
        safe_configuration({key: "synthetic-secret"})
