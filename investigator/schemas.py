import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


StatementType = Literal[
    "OBSERVATION",
    "DETERMINISTIC_RELATIONSHIP",
    "SOURCE_ATTRIBUTED_CONCLUSION",
    "POSSIBLE_EXPLANATION",
    "CONTRADICTION",
    "MISSING_INFORMATION",
    "INVESTIGATIVE_QUESTION",
    "LIMITATION",
    "TEMPORAL_PATTERN",
    "ASSUMPTION",
    "INSUFFICIENT_EVIDENCE",
]
GroundingStatus = Literal["ACCEPTED", "REJECTED_UNGROUNDED", "INSUFFICIENT_EVIDENCE", "REQUIRES_REVIEW"]
AnalysisStatus = Literal["COMPLETED", "COMPLETED_WITH_LIMITATIONS", "ABSTAINED_INSUFFICIENT_EVIDENCE", "FAILED_VALIDATION"]
AnalysisMode = Literal["standard", "leading_question_resistant", "abstention_check"]
TemporalMode = Literal["current", "event", "known"]


class SourceReference(BaseModel):
    reference_type: Literal["EVIDENCE", "OBSERVATION", "RETRIEVAL_RESULT", "GRAPH_RELATIONSHIP", "DETERMINISTIC_CONTEXT", "WORKSPACE_LIMITATION"]
    evidence_id: str | None = None
    evidence_identifier: str | None = None
    chunk_id: str | None = None
    observation_id: str | None = None
    retrieval_result_id: str | None = None
    graph_relationship_id: str | None = None
    source_anchor: dict[str, Any] = Field(default_factory=dict)
    temporal_context: dict[str, Any] = Field(default_factory=dict)
    context_path: str | None = None


class AnalysisItem(BaseModel):
    item_id: str
    semantic_type: StatementType
    statement: str
    rationale: str | None = None
    grounding_status: GroundingStatus = "ACCEPTED"
    source_references: list[SourceReference] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class InvestigationAnalysisRequest(BaseModel):
    tenant_id: uuid.UUID | None = None
    investigation_id: uuid.UUID
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    analysis_mode: AnalysisMode = "standard"
    investigator_question: str | None = Field(None, max_length=1000)
    retrieval_top_k: int = Field(8, ge=1, le=25)
    persist: bool = True


class InvestigationAnalysis(BaseModel):
    analysis_id: uuid.UUID
    investigation_id: uuid.UUID
    context_snapshot_id: str
    context_snapshot_version: str
    ai_execution_id: uuid.UUID | None = None
    status: AnalysisStatus
    observations: list[AnalysisItem] = Field(default_factory=list)
    relevant_changes: list[AnalysisItem] = Field(default_factory=list)
    temporal_patterns: list[AnalysisItem] = Field(default_factory=list)
    evidence_relationships: list[AnalysisItem] = Field(default_factory=list)
    possible_explanations: list[AnalysisItem] = Field(default_factory=list)
    contradictions: list[AnalysisItem] = Field(default_factory=list)
    missing_information: list[AnalysisItem] = Field(default_factory=list)
    questions_to_investigate: list[AnalysisItem] = Field(default_factory=list)
    limitations: list[AnalysisItem] = Field(default_factory=list)
    rejected_items: list[AnalysisItem] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    temporal_context: dict[str, Any]
    model_provenance: dict[str, Any]
    validation_summary: dict[str, Any]
    guardrails: dict[str, Any]
    created_at: datetime

    def accepted_items(self) -> list[AnalysisItem]:
        items: list[AnalysisItem] = []
        for collection in [
            self.observations,
            self.relevant_changes,
            self.temporal_patterns,
            self.evidence_relationships,
            self.possible_explanations,
            self.contradictions,
            self.missing_information,
            self.questions_to_investigate,
            self.limitations,
        ]:
            items.extend(collection)
        return items


class InvestigationAnalysisResponse(BaseModel):
    analysis: InvestigationAnalysis
    persisted: bool
    ai_execution_id: uuid.UUID | None = None
