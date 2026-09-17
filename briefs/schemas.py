import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel

class BriefCreateRequest(BaseModel):
    temporal_mode: Literal["current", "event", "known"] = "current"
    as_of: datetime | None = None
    generated_by: str = "MDARIX-Controlled-Brief-Assembler"

class BriefResponse(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    brief_version: int
    status: str
    title: str
    temporal_mode: str
    temporal_cutoff: datetime | None
    human_review_state: str
    content: dict[str, Any]
    provenance: dict[str, Any]
    limitations: dict[str, Any] | None
    created_at: datetime | None

class BriefListResponse(BaseModel):
    briefs: list[BriefResponse]
