from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.db.models.foundation import AIExecution, Investigation, ProductVersion, Scenario
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService, InvestigationWorkspaceError
from .schemas import ScenarioRequest


class ScenarioError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class ScenarioService:
    def __init__(self):
        self.workspace = InvestigationWorkspaceService()

    def execute(self, db: Session, tenant_id: UUID, investigation_id: UUID, request: ScenarioRequest, actor: str = "CONTROLLED_SCENARIO") -> dict:
        investigation = db.query(Investigation).filter(Investigation.tenant_id == tenant_id, Investigation.id == investigation_id).first()
        if not investigation:
            raise ScenarioError("INVESTIGATION_NOT_FOUND", "Investigation is not available for this tenant")
        if request.product_version_id and not db.query(ProductVersion.id).filter(
            ProductVersion.tenant_id == tenant_id,
            ProductVersion.id == request.product_version_id,
            ProductVersion.product_id == investigation.product_id,
        ).first():
            raise ScenarioError("PRODUCT_VERSION_NOT_FOUND", "ProductVersion is not available for this investigation product")
        try:
            baseline = self.workspace.workspace(db, InvestigationWorkspaceRequest(
                tenant_id=tenant_id, investigation_id=investigation_id,
                product_version_id=request.product_version_id,
                temporal_mode=request.temporal_mode, as_of=request.as_of,
                include_retrieval=True, retrieval_top_k=8,
            )).model_dump(mode="json")
        except InvestigationWorkspaceError as exc:
            raise ScenarioError(exc.code, exc.message) from exc

        evidence = baseline.get("evidence_context", [])
        relationships = baseline.get("relationship_context", {}).get("relationships", [])
        target = request.target.casefold()
        matched_evidence = [item for item in evidence if target in str(item).casefold()]
        matched_relationships = [item for item in relationships if target in str(item).casefold()]
        if request.scenario_type in {"EXCLUDE_RELATIONSHIP", "EXCLUDE_COHORT", "REMOVE_ASSUMPTION"} and not (matched_evidence or matched_relationships or target in str(baseline).casefold()):
            raise ScenarioError("TARGET_NOT_FOUND", "Scenario target is not present in the selected investigation context")

        result = {
            "classification": "SCENARIO_ANALYSIS",
            "status": "READY" if evidence else "INSUFFICIENT_EVIDENCE",
            "statement": "This is a scenario analysis based on stated assumptions. It does not change the observed record.",
            "scenario_type": request.scenario_type,
            "question": request.question,
            "temporal_context": baseline.get("temporal_context", {}),
            "baseline": {
                "investigation": baseline.get("investigation"),
                "evidence_count": len(evidence),
                "relationship_count": len(relationships),
            },
            "scenario": {
                "removed_or_modified_condition": request.target,
                "matched_evidence_count": len(matched_evidence),
                "matched_relationship_count": len(matched_relationships),
            },
            "comparison": "The observed record remains unchanged; the selected condition is evaluated only in derived context.",
            "supporting_evidence": matched_evidence,
            "contradicting_evidence": [],
            "unknowns": baseline.get("unknowns", []),
            "missing_evidence": ["Comparative evidence under the alternative condition is unavailable."],
            "limitations": baseline.get("limitations", []) + ["Scenario analysis does not establish causality or root cause."],
            "interpretation": "The selected assumption may weaken or change the explanation, but available evidence is insufficient to determine an alternative outcome.",
            "support_level": "NOT_A_CONFIDENCE_SCORE",
            "causality_claim": False,
            "root_cause_claim": False,
            "provenance": {"derived": True, "ground_truth_used": False, "tenant_id": str(tenant_id), "temporal_mode": request.temporal_mode},
            "human_review_required": True,
        }
        now = datetime.now(timezone.utc)
        execution = AIExecution(
            tenant_id=tenant_id, investigation_id=investigation_id, requestor_ref=actor,
            provider="deterministic-r1", model_name="controlled-scenario", model_version="day32",
            prompt_template_version="D32-1", orchestration_version="D32-1",
            context_refs={"investigation_id": str(investigation_id), "temporal_mode": request.temporal_mode},
            evidence_refs={"count": len(evidence)}, structured_input=request.model_dump(mode="json"),
            structured_output=result, rationale_summary=result["interpretation"],
            confidence_label="NOT_A_CONFIDENCE_SCORE", validation_status="VALIDATED", execution_timestamp=now,
        )
        db.add(execution)
        db.flush()
        scenario = Scenario(
            tenant_id=tenant_id, investigation_id=investigation_id,
            scenario_identifier=f"D32-{now.strftime('%Y%m%d%H%M%S%f')}", question=request.question,
            assumptions={"kind": "SCENARIO", "scenario_type": request.scenario_type, "request": request.model_dump(mode="json"), "result": result, "ai_execution_id": str(execution.id)},
            uncertainty=result["interpretation"], status=result["status"], created_at=now, updated_at=now,
        )
        if request.persist:
            db.add(scenario)
            db.commit()
            db.refresh(scenario)
            return {"id": scenario.id, "investigation_id": investigation_id, "status": scenario.status, "result": result, "created_at": scenario.created_at}
        db.rollback()
        return {"id": None, "investigation_id": investigation_id, "status": result["status"], "result": result, "created_at": now}
