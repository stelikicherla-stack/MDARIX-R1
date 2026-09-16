import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from investigator.schemas import SourceReference, TemporalMode


HypothesisStatus = Literal[
    "PROPOSED",
    "UNDER_INVESTIGATION",
    "SUPPORTED",
    "CONTRADICTED",
    "MIXED_EVIDENCE",
    "INSUFFICIENT_EVIDENCE",
    "REQUIRES_MORE_EVIDENCE",
    "REJECTED",
    "HUMAN_REVIEW_REQUIRED",
    "NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS",
]
EvidenceRelationshipType = Literal["SUPPORTS", "CONTRADICTS", "CONTEXTUAL", "INSUFFICIENT", "UNRESOLVED"]
TemporalConsistencyStatus = Literal["CONSISTENT", "PARTIALLY_CONSISTENT", "TEMPORAL_CONTRADICTION", "INSUFFICIENT_TEMPORAL_EVIDENCE"]
HumanReviewStatus = Literal["NOT_REVIEWED", "ACKNOWLEDGED", "MORE_EVIDENCE_REQUESTED", "REJECTED_BY_HUMAN", "RETAINED_FOR_INVESTIGATION"]


class HypothesisEvidenceRelationship(BaseModel):
    relationship_id: str
    relationship_type: EvidenceRelationshipType
    rationale: str
    source_references: list[SourceReference] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class Hypothesis(BaseModel):
    hypothesis_id: uuid.UUID
    investigation_id: uuid.UUID
    statement: str
    scope: str
    status: HypothesisStatus
    related_objects: list[dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: list[HypothesisEvidenceRelationship] = Field(default_factory=list)
    contradicting_evidence: list[HypothesisEvidenceRelationship] = Field(default_factory=list)
    contextual_evidence: list[HypothesisEvidenceRelationship] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    temporal_consistency: dict[str, Any]
    evidence_gaps: list[str] = Field(default_factory=list)
    falsification_conditions: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    context_snapshot: dict[str, Any]
    provenance: dict[str, Any]
    human_review_status: HumanReviewStatus = "NOT_REVIEWED"
    created_at: datetime
    updated_at: datetime


class HypothesisSetRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    investigator_question: str | None = Field(None, max_length=1000)
    regenerate: bool = True
    persist: bool = True


class HypothesisSet(BaseModel):
    hypothesis_set_id: uuid.UUID
    investigation_id: uuid.UUID
    source_analysis_id: uuid.UUID
    source_ai_execution_id: uuid.UUID | None = None
    context_snapshot_id: str
    context_snapshot_version: str
    status: HypothesisStatus
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    rejected_hypotheses: list[Hypothesis] = Field(default_factory=list)
    comparison: list[dict[str, Any]] = Field(default_factory=list)
    validation_summary: dict[str, Any]
    guardrails: dict[str, Any]
    provenance: dict[str, Any]
    created_at: datetime


class HypothesisSetResponse(BaseModel):
    hypothesis_set: HypothesisSet
    persisted: bool
    ai_execution_id: uuid.UUID | None = None
