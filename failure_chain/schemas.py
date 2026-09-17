import uuid
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field
from investigator.schemas import SourceReference, TemporalMode

LinkStatus=Literal["OBSERVED_SOURCE_SUPPORTED","DETERMINISTICALLY_DERIVED","HYPOTHESIZED","CONTRADICTED","UNKNOWN_GAP"]
ChainStatus=Literal["SUPPORTED_WITH_LIMITATIONS","BROKEN_CHAIN","MIXED_EVIDENCE","ABSTAINED","REQUIRES_HUMAN_REVIEW"]
class FailureChainLink(BaseModel):
    link_id: str = Field(default_factory=lambda: f"FCL-{uuid.uuid4().hex[:12]}")
    sequence: int
    from_entity_or_state: str
    relationship: str
    to_entity_or_state: str
    epistemic_status: LinkStatus
    evidence_references: list[SourceReference] = Field(default_factory=list)
    contradictions: list[SourceReference] = Field(default_factory=list)
    unknowns: list[uuid.UUID] = Field(default_factory=list)
    temporal_context: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
class FailureChain(BaseModel):
    chain_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    hypothesis_id: uuid.UUID | None = None
    chain_statement: str
    start_state: str
    end_state: str
    links: list[FailureChainLink] = Field(default_factory=list)
    branches: list[list[str]] = Field(default_factory=list)
    unresolved_links: list[str] = Field(default_factory=list)
    contradictory_links: list[str] = Field(default_factory=list)
    temporal_consistency: dict[str, Any] = Field(default_factory=dict)
    overall_status: ChainStatus
    limitations: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    human_review_status: str = "NOT_REVIEWED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class FailureChainSet(BaseModel):
    failure_chain_set_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    source_hypothesis_set_id: uuid.UUID
    source_unknown_set_id: uuid.UUID | None = None
    context_snapshot_id: str
    context_snapshot_version: str
    chains: list[FailureChain] = Field(default_factory=list)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    guardrails: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class FailureChainRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    hypothesis_set_id: uuid.UUID | None = None
    unknown_set_id: uuid.UUID | None = None
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    persist: bool = True
class FailureChainResponse(BaseModel):
    failure_chain_set: FailureChainSet
    persisted: bool
    ai_execution_id: uuid.UUID | None = None
