import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field
from investigator.schemas import SourceReference, TemporalMode

ChallengeType = Literal["EVIDENCE_SUFFICIENCY","CONTRADICTORY_EVIDENCE","TEMPORAL_INCONSISTENCY","CAUSAL_LEAP","MISSING_EVIDENCE","UNSUPPORTED_ASSUMPTION","ALTERNATIVE_EXPLANATION","CONFOUNDING_FACTOR","SELECTIVE_EVIDENCE","OVERGENERALIZATION","PREMATURE_CONVERGENCE","TRACEABILITY_GAP","POPULATION_MISMATCH","VERSION_MISMATCH","HISTORICAL_KNOWLEDGE_LIMITATION","INSUFFICIENT_COMPARATIVE_EVIDENCE"]
ChallengeStatus = Literal["OPEN","MATERIAL","NON_MATERIAL","RESOLVED_BY_EVIDENCE","REQUIRES_MORE_EVIDENCE","REQUIRES_HUMAN_REVIEW","NOT_APPLICABLE"]

class InvestigationChallenge(BaseModel):
    challenge_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    hypothesis_id: uuid.UUID | None = None
    challenge_type: ChallengeType
    statement: str
    rationale: str
    evidence_references: list[SourceReference] = Field(default_factory=list)
    contradiction_references: list[SourceReference] = Field(default_factory=list)
    affected_assumptions: list[str] = Field(default_factory=list)
    temporal_issue: dict[str, Any] | None = None
    alternative_explanation_reference: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    severity: Literal["LOW","MEDIUM","HIGH","CRITICAL"] = "MEDIUM"
    materiality: Literal["MATERIAL","NON_MATERIAL"] = "NON_MATERIAL"
    status: ChallengeStatus = "OPEN"
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    human_review_status: str = "NOT_REVIEWED"
    created_at: datetime = Field(default_factory=lambda: datetime.now().astimezone())

class ChallengeSet(BaseModel):
    challenge_set_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    source_hypothesis_set_id: uuid.UUID
    context_snapshot_id: str
    context_snapshot_version: str
    challenges: list[InvestigationChallenge] = Field(default_factory=list)
    no_material_challenge: bool = False
    abstained: bool = False
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    guardrails: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class ChallengeRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    hypothesis_set_id: uuid.UUID | None = None
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    user_question: str | None = Field(None, max_length=1000)
    persist: bool = True

class ChallengeResponse(BaseModel):
    challenge_set: ChallengeSet
    persisted: bool
    ai_execution_id: uuid.UUID | None = None
