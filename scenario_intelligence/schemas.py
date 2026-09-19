from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

ScenarioType = Literal[
    "EXCLUDE_RELATIONSHIP", "EXCLUDE_COHORT", "REMOVE_ASSUMPTION",
    "ALTERNATIVE_EXPLANATION", "EVIDENCE_SENSITIVITY",
    "TRACEABILITY_LIMITATION", "TEMPORAL_COMPARISON", "HYPOTHESIS_STRESS_TEST",
]
TemporalMode = Literal["current", "event", "known"]


class ScenarioRequest(BaseModel):
    scenario_type: ScenarioType
    question: str = Field(min_length=1, max_length=2000)
    target: str = Field(min_length=1, max_length=255)
    temporal_mode: TemporalMode = "current"
    as_of: datetime | None = None
    product_version_id: UUID | None = None
    persist: bool = False

    @model_validator(mode="after")
    def validate_temporal(self):
        if self.temporal_mode == "current" and self.as_of is not None:
            raise ValueError("current context cannot include as_of")
        if self.temporal_mode != "current" and self.as_of is None:
            raise ValueError("historical context requires as_of")
        return self


class ScenarioResponse(BaseModel):
    id: UUID | None
    investigation_id: UUID
    status: str
    result: dict[str, Any]
    created_at: datetime | None = None
