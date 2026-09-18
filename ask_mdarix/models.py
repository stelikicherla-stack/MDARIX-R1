from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterpretationStatus(StrEnum):
    READY = "READY"
    REQUIRES_CLARIFICATION = "REQUIRES_CLARIFICATION"
    NOT_FOUND = "NOT_FOUND"
    INVALID = "INVALID"


class TemporalMode(StrEnum):
    CURRENT = "CURRENT"
    EVENT_AS_OF = "EVENT_AS_OF"
    KNOWN_AS_OF = "KNOWN_AS_OF"


class InvestigationSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    tenant_id: str
    authorized_user_id: str
    status: str = "ACTIVE"
    active_product_id: str | None = None
    active_product_version_id: str | None = None
    correlation_id: str


class InvestigationQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    session_id: str
    tenant_id: str
    user_id: str
    raw_question: str = Field(min_length=1, max_length=2000)
    normalized_question: str
    correlation_id: str


class InvestigationSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    status: InterpretationStatus
    normalized_question: str
    product_query: str | None = None
    version_queries: list[str] = Field(default_factory=list)
    temporal_mode: TemporalMode = TemporalMode.CURRENT
    event_start: date | None = None
    event_end: date | None = None
    knowledge_time: date | None = None
    requested_entities: list[str] = Field(default_factory=list)
    requested_metrics: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    retrieval_scope: dict[str, Any] = Field(default_factory=dict)

