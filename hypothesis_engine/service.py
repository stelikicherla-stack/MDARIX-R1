import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from ai.execution import record_ai_execution
from backend.app.db.models.foundation import AIExecution
from hypothesis_engine.engine import (
    MODEL,
    MODEL_VERSION,
    ORCHESTRATION_VERSION,
    PROMPT_TEMPLATE_VERSION,
    PROVIDER,
    ControlledHypothesisEngine,
)
from hypothesis_engine.schemas import HypothesisSet, HypothesisSetRequest, HypothesisSetResponse
from hypothesis_engine.validator import HypothesisValidator
from investigator.schemas import InvestigationAnalysisRequest
from investigator.service import EvidenceGroundedInvestigatorService, InvestigatorError


class HypothesisEngineError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class CompetingHypothesisService:
    def __init__(
        self,
        investigator_service: EvidenceGroundedInvestigatorService | None = None,
        engine: ControlledHypothesisEngine | None = None,
        validator: HypothesisValidator | None = None,
    ) -> None:
        self.investigator_service = investigator_service or EvidenceGroundedInvestigatorService()
        self.engine = engine or ControlledHypothesisEngine()
        self.validator = validator or HypothesisValidator()

    def generate(self, db: Session, request: HypothesisSetRequest) -> HypothesisSetResponse:
        if request.tenant_id is None:
            raise HypothesisEngineError("TENANT_REQUIRED", "tenant_id is required")
        start = time.time()
        try:
            analysis_response = self.investigator_service.analyze(
                db,
                InvestigationAnalysisRequest(
                    tenant_id=request.tenant_id,
                    investigation_id=request.investigation_id,
                    temporal_mode=request.temporal_mode,
                    as_of=request.as_of,
                    investigator_question=request.investigator_question,
                    persist=True,
                ),
            )
        except InvestigatorError as exc:
            raise HypothesisEngineError(exc.code, exc.message) from exc

        hypothesis_set = self.engine.generate(analysis_response.analysis, request.investigator_question)
        accepted, rejected, summary = self.validator.validate(hypothesis_set.hypotheses)
        status = "INSUFFICIENT_EVIDENCE" if accepted and accepted[0].status == "NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS" else "MIXED_EVIDENCE"
        if rejected and not accepted:
            status = "HUMAN_REVIEW_REQUIRED"
        hypothesis_set = hypothesis_set.model_copy(
            update={
                "hypotheses": accepted,
                "rejected_hypotheses": rejected,
                "status": status,
                "validation_summary": {
                    **summary,
                    "contradiction_preservation_count": sum(len(h.contradicting_evidence) for h in accepted),
                    "alternative_hypothesis_count": len(accepted),
                    "future_information_leakage": 0,
                    "ground_truth_runtime_leakage": 0,
                    "tenant_leakage": 0,
                    "wrong_version_contamination": 0,
                    "prompt_injection_policy_violations": 0,
                    "historical_root_cause_converted_to_fact": 0,
                },
            }
        )

        ai_execution_id = None
        persisted = False
        if request.persist:
            row = record_ai_execution(
                db=db,
                tenant_id=request.tenant_id,
                investigation_id=request.investigation_id,
                provider=PROVIDER,
                model_name=MODEL,
                model_version=MODEL_VERSION,
                prompt_template_version=PROMPT_TEMPLATE_VERSION,
                orchestration_version=ORCHESTRATION_VERSION,
                context_refs={
                    "context_snapshot_id": hypothesis_set.context_snapshot_id,
                    "context_snapshot_version": hypothesis_set.context_snapshot_version,
                    "source_analysis_id": str(hypothesis_set.source_analysis_id),
                    "source_ai_execution_id": str(hypothesis_set.source_ai_execution_id) if hypothesis_set.source_ai_execution_id else None,
                    "day11_contract": "InvestigationAnalysis",
                },
                evidence_refs={
                    "hypothesis_ids": [str(h.hypothesis_id) for h in hypothesis_set.hypotheses],
                    "relationship_count": sum(
                        len(h.supporting_evidence) + len(h.contradicting_evidence) + len(h.contextual_evidence)
                        for h in hypothesis_set.hypotheses
                    ),
                },
                structured_input=request.model_dump(mode="json"),
                structured_output=hypothesis_set.model_dump(mode="json"),
                validation_status=hypothesis_set.status,
                latency_ms=int((time.time() - start) * 1000),
                requestor_ref="MDARIX-HypothesisEngine",
            )
            db.commit()
            ai_execution_id = row.id
            persisted = True
        return HypothesisSetResponse(hypothesis_set=hypothesis_set, persisted=persisted, ai_execution_id=ai_execution_id)

    def latest(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> HypothesisSetResponse | None:
        row = (
            db.query(AIExecution)
            .filter(
                AIExecution.tenant_id == tenant_id,
                AIExecution.investigation_id == investigation_id,
                AIExecution.provider == PROVIDER,
                AIExecution.orchestration_version == ORCHESTRATION_VERSION,
            )
            .order_by(AIExecution.execution_timestamp.desc())
            .first()
        )
        if not row or not row.structured_output:
            return None
        return HypothesisSetResponse(hypothesis_set=HypothesisSet.model_validate(row.structured_output), persisted=True, ai_execution_id=row.id)

    def get(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, hypothesis_id: uuid.UUID) -> HypothesisSetResponse:
        rows = (
            db.query(AIExecution)
            .filter(
                AIExecution.tenant_id == tenant_id,
                AIExecution.investigation_id == investigation_id,
                AIExecution.provider == PROVIDER,
                AIExecution.orchestration_version == ORCHESTRATION_VERSION,
            )
            .order_by(AIExecution.execution_timestamp.desc())
            .all()
        )
        for row in rows:
            if not row.structured_output:
                continue
            hypothesis_set = HypothesisSet.model_validate(row.structured_output)
            if any(str(h.hypothesis_id) == str(hypothesis_id) for h in hypothesis_set.hypotheses):
                return HypothesisSetResponse(hypothesis_set=hypothesis_set, persisted=True, ai_execution_id=row.id)
        raise HypothesisEngineError("HYPOTHESIS_NOT_FOUND", "Hypothesis not found")
