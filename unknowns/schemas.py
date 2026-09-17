import uuid
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field
from investigator.schemas import SourceReference, TemporalMode

UnknownCategory = Literal["MISSING_EVIDENCE","UNRESOLVED_IDENTITY","INCOMPLETE_TRACEABILITY","CONTRADICTORY_EVIDENCE","TEMPORAL_UNCERTAINTY","MISSING_COMPARATIVE_EVIDENCE","UNVERIFIED_ASSUMPTION","MISSING_TEST_RESULT","MISSING_MANUFACTURING_CONTEXT","MISSING_SUPPLIER_CONTEXT","MISSING_CONFIGURATION_CONTEXT","MISSING_POPULATION_CONTEXT","UNRESOLVED_HYPOTHESIS","UNRESOLVED_CHALLENGE","INACCESSIBLE_INFORMATION","NOT_AVAILABLE_AT_RELEVANT_TIME","INSUFFICIENT_EVIDENCE"]
UnknownStatus = Literal["OPEN","PARTIALLY_RESOLVED","RESOLVED","UNRESOLVABLE_WITH_AVAILABLE_DATA","REQUIRES_EXTERNAL_EVIDENCE","REQUIRES_HUMAN_REVIEW","NOT_APPLICABLE"]

class InvestigationUnknown(BaseModel):
    unknown_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    hypothesis_id: uuid.UUID | None = None
    challenge_id: uuid.UUID | None = None
    category: UnknownCategory
    statement: str
    why_it_matters: str
    related_entities: list[dict[str, Any]] = Field(default_factory=list)
    related_evidence: list[SourceReference] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    temporal_context: dict[str, Any] = Field(default_factory=dict)
    resolution_requirement: str
    resolution_source_type: str
    status: UnknownStatus = "OPEN"
    materiality: Literal["MATERIAL","NON_MATERIAL"] = "MATERIAL"
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    human_review_status: str = "NOT_REVIEWED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UnknownSet(BaseModel):
    unknown_set_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    source_hypothesis_set_id: uuid.UUID
    source_challenge_set_id: uuid.UUID | None = None
    context_snapshot_id: str
    context_snapshot_version: str
    unknowns: list[InvestigationUnknown] = Field(default_factory=list)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    guardrails: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UnknownRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    hypothesis_set_id: uuid.UUID | None = None
    challenge_set_id: uuid.UUID | None = None
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    persist: bool = True

class UnknownResponse(BaseModel):
    unknown_set: UnknownSet
    persisted: bool
    ai_execution_id: uuid.UUID | None = None
