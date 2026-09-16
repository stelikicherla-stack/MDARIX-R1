import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from retrieval.schemas import RetrievalResponse


WorkspaceTemporalMode = Literal["current", "event", "known"]


class InvestigationWorkspaceRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    temporal_mode: WorkspaceTemporalMode = "current"
    as_of: datetime | None = None
    include_retrieval: bool = True
    retrieval_top_k: int = Field(8, ge=1, le=25)


class InvestigationWorkspaceResponse(BaseModel):
    investigation: dict[str, Any]
    product_context: dict[str, Any]
    temporal_context: dict[str, Any]
    relationship_context: dict[str, Any]
    evidence_context: list[dict[str, Any]]
    retrieval_context: RetrievalResponse | None
    limitations: list[dict[str, Any]]
    guardrails: dict[str, Any]
    metadata: dict[str, Any]
