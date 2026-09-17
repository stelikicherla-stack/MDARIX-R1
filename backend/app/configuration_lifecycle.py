from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class ConfigurationVersion:
    tenant_id: str; configuration_id: str; version: int; status: str = "DRAFT"; reason: str = ""

class ConfigurationLifecycle:
    transitions: ClassVar[dict[str, set[str]]] = {"DRAFT":{"VALIDATED"}, "VALIDATED":{"APPROVED"}, "APPROVED":{"ACTIVE"}, "ACTIVE":{"SUPERSEDED"}, "SUPERSEDED":set()}
    def transition(self, config: ConfigurationVersion, target: str, *, authorized: bool, tenant_id: str) -> ConfigurationVersion:
        if tenant_id != config.tenant_id: raise PermissionError("TENANT_CONTEXT_MISMATCH")
        if not authorized: raise PermissionError("AUTHORIZATION_REQUIRED")
        if target not in self.transitions.get(config.status, set()): raise ValueError(f"INVALID_TRANSITION:{config.status}->{target}")
        return ConfigurationVersion(config.tenant_id, config.configuration_id, config.version, target, config.reason)
