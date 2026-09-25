"""Safety rules for persisted connector and mapping configuration."""

SENSITIVE_KEY_PARTS = ("password", "token", "secret", "credential", "private_key", "cookie", "authorization")


def validate_safe_configuration(value: object, path: str = "configuration") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            # A reference to a managed secret is configuration metadata, not a
            # secret value. The referenced value must never be persisted.
            if normalized in {"credential_ref", "secret_ref", "vault_ref"}:
                if not isinstance(nested, str) or not nested.replace("_", "").isalnum() or len(nested) > 120:
                    raise ValueError(f"INVALID_SECRET_REFERENCE:{path}.{key}")
                continue
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                raise ValueError(f"SENSITIVE_CONFIGURATION_FIELD:{path}.{key}")
            validate_safe_configuration(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            validate_safe_configuration(nested, f"{path}[{index}]")


def safe_configuration(value: dict) -> dict:
    validate_safe_configuration(value)
    return value
