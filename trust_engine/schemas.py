import uuid
from datetime import datetime
from pydantic import BaseModel
class AssuranceRequest(BaseModel):
    output_type: str = "AI_EXECUTION"
    output_id: str | None = None
class AssuranceCheckResponse(BaseModel):
    check_type: str; status: str; severity: str; message: str; details: dict | None = None
class AssuranceResponse(BaseModel):
    id: uuid.UUID; ai_execution_id: uuid.UUID; status: str; assurance_version: int; trust_policy_version: str; human_review_required: bool; revalidation_required: bool; configuration_hash: str | None; checks: list[AssuranceCheckResponse]; limitations: dict | None = None; generated_at: datetime | None = None
