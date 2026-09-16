import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


RetrievalMode = Literal["structured", "semantic", "hybrid"]
TemporalMode = Literal["current", "event", "known"]


class RetrievalRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=2000)
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    product_version_id: uuid.UUID | None = None
    component_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    lot_id: uuid.UUID | None = None
    complaint_id: uuid.UUID | None = None
    evidence_types: list[str] = Field(default_factory=list)
    event_as_of: datetime | None = None
    knowledge_as_of: datetime | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    top_k: int = Field(10, ge=1, le=50)
    retrieval_mode: RetrievalMode = "hybrid"
    temporal_mode: TemporalMode = "current"

    @field_validator("query_text")
    @classmethod
    def query_must_have_terms(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query_text must not be empty")
        return stripped


class RetrievalResult(BaseModel):
    result_id: str
    evidence_id: uuid.UUID
    evidence_identifier: str
    evidence_type: str
    evidence_title: str
    chunk_id: uuid.UUID
    chunk_sequence_number: int
    source_anchor: dict[str, Any]
    excerpt: str
    retrieval_method: RetrievalMode | Literal["structured", "semantic", "hybrid"]
    retrieval_score: float
    structured_match_reasons: list[str]
    related_entities: list[dict[str, Any]]
    temporal_context: dict[str, Any]
    evidence_available: bool
    quality_limitations: list[str]
    provenance: dict[str, Any]


class RetrievalResponse(BaseModel):
    retrieval_query_id: uuid.UUID
    status: Literal["COMPLETED", "NO_RELEVANT_EVIDENCE", "INSUFFICIENT_RELEVANT_EVIDENCE"]
    query_text: str
    retrieval_mode: RetrievalMode
    temporal_mode: TemporalMode
    top_k: int
    results_count: int
    results: list[RetrievalResult]
    limitations: list[str] = Field(default_factory=list)
