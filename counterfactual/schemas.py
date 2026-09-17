from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


SUPPORTED_INTERVENTIONS = (
    "REMOVE_CHANGE",
    "REPLACE_COMPONENT_REVISION",
    "REMOVE_SUPPLIER_CHANGE",
    "REMOVE_FAILURE_CHAIN_LINK",
    "REMOVE_HYPOTHESIZED_RELATIONSHIP",
    "COMPARE_HYPOTHESES",
    "TEST_TEMPORAL_DEPENDENCY",
)


class CounterfactualRequest(BaseModel):
    temporal_mode: str = Field("current", pattern="^(current|event|known)$")
    as_of: datetime | None = None
    intervention_type: str
    intervention_target: str = Field(min_length=1, max_length=255)
    intervention_description: str = Field(min_length=1, max_length=2000)
    hypothesis_id: UUID | None = None
    failure_chain_id: UUID | None = None

    @field_validator("intervention_type")
    @classmethod
    def supported_intervention(cls, value: str) -> str:
        if value not in SUPPORTED_INTERVENTIONS:
            raise ValueError("unsupported intervention type")
        return value

    @model_validator(mode="after")
    def valid_temporal_context(self):
        if self.temporal_mode == "current" and self.as_of is not None:
            raise ValueError("current context cannot include as_of")
        if self.temporal_mode != "current" and self.as_of is None:
            raise ValueError("historical context requires as_of")
        return self


class CounterfactualResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    status: str
    result: dict[str, Any]
    created_at: datetime | None
