import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ai.execution import record_ai_execution
from backend.app.db.models.foundation import AIExecution
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceError, InvestigationWorkspaceService
from investigator.grounding import GroundingValidator
from investigator.provider import (
    MODEL,
    MODEL_VERSION,
    ORCHESTRATION_VERSION,
    PROMPT_TEMPLATE_VERSION,
    PROVIDER,
    ControlledInvestigatorProvider,
)
from investigator.schemas import AnalysisItem, InvestigationAnalysis, InvestigationAnalysisRequest, InvestigationAnalysisResponse


class InvestigatorError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class EvidenceGroundedInvestigatorService:
    def __init__(
        self,
        workspace_service: InvestigationWorkspaceService | None = None,
        provider: ControlledInvestigatorProvider | None = None,
        grounding_validator: GroundingValidator | None = None,
    ) -> None:
        self.workspace_service = workspace_service or InvestigationWorkspaceService()
        self.provider = provider or ControlledInvestigatorProvider()
        self.grounding_validator = grounding_validator or GroundingValidator()

    def analyze(self, db: Session, request: InvestigationAnalysisRequest) -> InvestigationAnalysisResponse:
        if request.tenant_id is None:
            raise InvestigatorError("TENANT_REQUIRED", "tenant_id is required")

        start = time.time()
        try:
            workspace = self.workspace_service.workspace(
                db,
                InvestigationWorkspaceRequest(
                    tenant_id=request.tenant_id,
                    investigation_id=request.investigation_id,
                    temporal_mode=request.temporal_mode,
                    as_of=request.as_of,
                    include_retrieval=True,
                    retrieval_top_k=request.retrieval_top_k,
                ),
            )
        except InvestigationWorkspaceError as exc:
            raise InvestigatorError(exc.code, exc.message) from exc

        analysis = self.provider.analyze(
            workspace=workspace,
            analysis_id=uuid.uuid4(),
            investigator_question=request.investigator_question,
            analysis_mode=request.analysis_mode,
        )
        analysis = self._validate_analysis(analysis)
        from genai.grounding import advisory, build_authorized_context
        grounded = build_authorized_context(db, tenant_id=request.tenant_id, investigation_id=request.investigation_id, temporal_mode=request.temporal_mode, as_of=request.as_of)
        ai_advisory = advisory(workflow="INVESTIGATION_SYNTHESIS", deterministic_result=analysis.model_dump(mode="json"), grounded_context=grounded, question=request.investigator_question)
        analysis = analysis.model_copy(update={"model_provenance": {**analysis.model_provenance, "live_provider_advisory": ai_advisory}})
        persisted = False
        ai_execution_id = None

        if request.persist:
            exec_record = record_ai_execution(
                db=db,
                tenant_id=request.tenant_id,
                investigation_id=request.investigation_id,
                provider=PROVIDER,
                model_name=MODEL,
                model_version=MODEL_VERSION,
                prompt_template_version=PROMPT_TEMPLATE_VERSION,
                orchestration_version=ORCHESTRATION_VERSION,
                context_refs={
                    "context_snapshot_id": analysis.context_snapshot_id,
                    "context_snapshot_version": analysis.context_snapshot_version,
                    "workspace_version": workspace.metadata.get("workspace_version"),
                    "temporal_context": workspace.temporal_context,
                    "day10_contract": "InvestigationWorkspaceResponse",
                },
                evidence_refs={
                    "evidence_identifiers": [evidence.get("evidence_identifier") for evidence in workspace.evidence_context],
                    "retrieval_query_id": str(workspace.retrieval_context.retrieval_query_id) if workspace.retrieval_context else None,
                },
                structured_input={
                    "investigation_id": str(request.investigation_id),
                    "temporal_mode": request.temporal_mode,
                    "as_of": request.as_of.isoformat() if request.as_of else None,
                    "analysis_mode": request.analysis_mode,
                    "investigator_question_present": bool(request.investigator_question),
                    "retrieval_top_k": request.retrieval_top_k,
                },
                structured_output=analysis.model_dump(mode="json"),
                validation_status=analysis.status,
                latency_ms=int((time.time() - start) * 1000),
                error_state=None if analysis.status != "FAILED_VALIDATION" else "Grounding validation rejected material statements",
                requestor_ref="MDARIX-AI-Investigator",
            )
            analysis.ai_execution_id = exec_record.id
            exec_record.structured_output = analysis.model_dump(mode="json")
            db.commit()
            persisted = True
            ai_execution_id = exec_record.id

        return InvestigationAnalysisResponse(analysis=analysis, persisted=persisted, ai_execution_id=ai_execution_id)

    def latest(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> InvestigationAnalysisResponse | None:
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
        analysis = InvestigationAnalysis.model_validate(row.structured_output)
        analysis.ai_execution_id = row.id
        return InvestigationAnalysisResponse(analysis=analysis, persisted=True, ai_execution_id=row.id)

    def get(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, analysis_id: uuid.UUID) -> InvestigationAnalysisResponse:
        rows = (
            db.query(AIExecution)
            .filter(
                AIExecution.tenant_id == tenant_id,
                AIExecution.investigation_id == investigation_id,
                AIExecution.provider == PROVIDER,
                AIExecution.orchestration_version == ORCHESTRATION_VERSION,
            )
            .all()
        )
        for row in rows:
            if row.structured_output and row.structured_output.get("analysis_id") == str(analysis_id):
                analysis = InvestigationAnalysis.model_validate(row.structured_output)
                analysis.ai_execution_id = row.id
                return InvestigationAnalysisResponse(analysis=analysis, persisted=True, ai_execution_id=row.id)
        raise InvestigatorError("ANALYSIS_NOT_FOUND", "Investigation analysis not found")

    def _validate_analysis(self, analysis: InvestigationAnalysis) -> InvestigationAnalysis:
        accepted, rejected, summary = self.grounding_validator.validate_items(analysis.accepted_items())
        grouped = self._regroup(accepted)
        evidence_denominator = summary["evidence_derived_items"]
        evidence_coverage = 1.0 if evidence_denominator == 0 else summary["evidence_derived_items_with_source_anchor"] / evidence_denominator
        material_coverage = 1.0 if summary["material_items"] == 0 else summary["accepted_items"] / summary["material_items"]
        status = "COMPLETED_WITH_LIMITATIONS"
        if rejected:
            status = "FAILED_VALIDATION"
        elif any(item.semantic_type == "INSUFFICIENT_EVIDENCE" for item in grouped["limitations"] + grouped["missing_information"]):
            status = "ABSTAINED_INSUFFICIENT_EVIDENCE"

        return analysis.model_copy(
            update={
                **grouped,
                "rejected_items": rejected,
                "status": status,
                "validation_summary": {
                    **summary,
                    "material_grounding_coverage": material_coverage,
                    "evidence_source_anchor_coverage": evidence_coverage,
                    "invented_evidence_count": len(rejected),
                    "unsupported_causal_conclusions": self._unsupported_causal_conclusions(accepted),
                    "validated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    def _regroup(self, accepted: list[AnalysisItem]) -> dict[str, list[AnalysisItem]]:
        groups: dict[str, list[AnalysisItem]] = {
            "observations": [],
            "relevant_changes": [],
            "temporal_patterns": [],
            "evidence_relationships": [],
            "possible_explanations": [],
            "contradictions": [],
            "missing_information": [],
            "questions_to_investigate": [],
            "limitations": [],
        }
        mapping = {
            "OBSERVATION": "observations",
            "SOURCE_ATTRIBUTED_CONCLUSION": "observations",
            "TEMPORAL_PATTERN": "temporal_patterns",
            "DETERMINISTIC_RELATIONSHIP": "evidence_relationships",
            "POSSIBLE_EXPLANATION": "possible_explanations",
            "CONTRADICTION": "contradictions",
            "MISSING_INFORMATION": "missing_information",
            "INVESTIGATIVE_QUESTION": "questions_to_investigate",
            "LIMITATION": "limitations",
            "ASSUMPTION": "limitations",
            "INSUFFICIENT_EVIDENCE": "limitations",
        }
        for item in accepted:
            groups[mapping.get(item.semantic_type, "limitations")].append(item)
        return groups

    def _unsupported_causal_conclusions(self, items: list[AnalysisItem]) -> int:
        forbidden = ["caused the shutdown", "root cause is", "establishes causality", "proven causal"]
        count = 0
        for item in items:
            text = item.statement.lower()
            if item.semantic_type != "SOURCE_ATTRIBUTED_CONCLUSION" and any(term in text for term in forbidden):
                count += 1
        return count
