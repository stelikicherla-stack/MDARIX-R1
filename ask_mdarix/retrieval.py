from dataclasses import dataclass
from .models import InvestigationSpecification, InterpretationStatus


ALLOWED_ENTITIES = frozenset({"Complaint", "Evidence", "Change", "Investigation", "Unknown", "Product", "ProductVersion"})


@dataclass(frozen=True)
class RetrievalPlan:
    entities: tuple[str, ...]
    limit: int
    tenant_scoped: bool
    authorized_only: bool
    temporal_mode: str
    product_version_scope: tuple[str, ...]
    status: str
    limitation: str | None = None


def build_retrieval_plan(spec: InvestigationSpecification, *, max_records: int = 100) -> RetrievalPlan:
    if spec.status is not InterpretationStatus.READY:
        return RetrievalPlan((), 0, True, True, spec.temporal_mode.value, tuple(spec.version_queries), "NOT_EXECUTABLE", "Clarification or validation is required")
    entities = tuple(entity for entity in spec.requested_entities if entity in ALLOWED_ENTITIES) or ("Investigation",)
    bounded = max(1, min(max_records, 1000))
    return RetrievalPlan(entities, bounded, True, True, spec.temporal_mode.value, tuple(spec.version_queries), "READY")
