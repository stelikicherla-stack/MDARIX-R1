import datetime
import logging
import time
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.db.models.foundation import AIExecution

logger = logging.getLogger(__name__)


def record_ai_execution(
    db: Session,
    tenant_id: uuid.UUID,
    provider: str,
    model_name: str,
    model_version: Optional[str] = None,
    prompt_template_version: Optional[str] = "1.0",
    orchestration_version: Optional[str] = "R1-Day8",
    investigation_id: Optional[uuid.UUID] = None,
    context_refs: Optional[Dict[str, Any]] = None,
    evidence_refs: Optional[Dict[str, Any]] = None,
    structured_input: Optional[Dict[str, Any]] = None,
    structured_output: Optional[Dict[str, Any]] = None,
    validation_status: str = "VALIDATED",
    latency_ms: Optional[int] = None,
    error_state: Optional[str] = None,
) -> AIExecution:
    """Records full provenance of an AI execution into the ai_executions table without hidden chain-of-thought."""
    execution_record = AIExecution(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        investigation_id=investigation_id,
        requestor_ref="MDARIX-EvidenceIntelligence",
        provider=provider,
        model_name=model_name,
        model_version=model_version or "latest",
        prompt_template_version=prompt_template_version,
        orchestration_version=orchestration_version,
        context_refs=context_refs,
        evidence_refs=evidence_refs,
        structured_input=structured_input,
        structured_output=structured_output,
        validation_status=validation_status,
        execution_timestamp=datetime.datetime.now(datetime.timezone.utc),
        latency_ms=latency_ms or 0,
        error_state=error_state,
    )

    db.add(execution_record)
    db.flush()
    return execution_record
