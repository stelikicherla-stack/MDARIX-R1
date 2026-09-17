from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DecisionContextRequest(BaseModel):
    temporal_mode: str = Field("current", pattern="^(current|event|known)$")
    as_of: datetime | None = None


class AdvisoryRequest(DecisionContextRequest):
    decision_question: str = "What action is currently supportable from the controlled investigation context?"


class DecisionCreateRequest(DecisionContextRequest):
    decision_type: str = "INVESTIGATION_DISPOSITION"
    selected_action: str
    rationale: str = Field(min_length=1, max_length=10000)
    authorized_by_ref: str = Field(min_length=1, max_length=255)


class ReviewCreateRequest(BaseModel):
    disposition: str = Field(min_length=1, max_length=80)
    comments: str | None = Field(default=None, max_length=10000)
    reviewer_ref: str = Field(min_length=1, max_length=255)


class DecisionResponse(BaseModel):
    id: UUID
    decision_identifier: str
    decision_type: str
    decision_status: str
    decision_readiness: str | None
    selected_action: str | None
    human_decision: str | None
    rationale: str
    authorized_by_ref: str
    decision_timestamp: datetime
    temporal_context: dict[str, Any] | None
    limitations: dict[str, Any] | None
    advisory_execution_id: UUID | None
