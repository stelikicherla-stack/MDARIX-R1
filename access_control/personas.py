"""Canonical R1 persona catalog and safe assignment validation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaDefinition:
    code: str
    label: str
    dashboard_emphasis: tuple[str, ...]


R1_PERSONAS = (
    PersonaDefinition("INVESTIGATOR", "Quality/PMS Investigator", ("signals", "investigations", "evidence_gaps", "unknowns")),
    PersonaDefinition("PRODUCT_QUALITY", "Product/Design Quality Engineer", ("products", "revisions", "components", "suppliers", "changes")),
    PersonaDefinition("REVIEWER", "Regulatory/PMS Reviewer", ("evidence_completeness", "provenance", "contradictions", "limitations")),
    PersonaDefinition("APPROVER", "Quality/Regulatory Approver", ("decision_briefs", "authority", "segregation_of_duties", "material_changes")),
    PersonaDefinition("LEADER", "Product/Quality Leader", ("portfolio_signals", "aging", "decision_load", "risk")),
    PersonaDefinition("ADMINISTRATOR", "MDARIX Administrator", ("users", "roles", "connectors", "mappings", "plans", "audit")),
)

PERSONAS_BY_CODE = {persona.code: persona for persona in R1_PERSONAS}


def get_persona(code: str) -> PersonaDefinition:
    try:
        return PERSONAS_BY_CODE[code.strip().upper()]
    except (AttributeError, KeyError) as exc:
        raise ValueError("UNKNOWN_PERSONA") from exc


def validate_persona_assignments(codes: list[str]) -> list[PersonaDefinition]:
    """Validate and normalize assignments without granting authority."""
    normalized = [code.strip().upper() for code in codes]
    if len(normalized) != len(set(normalized)):
        raise ValueError("DUPLICATE_PERSONA")
    return [get_persona(code) for code in normalized]
