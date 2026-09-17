from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.db.models.foundation import AIExecution, Investigation, Scenario
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService
from .schemas import CounterfactualRequest, SUPPORTED_INTERVENTIONS


class CounterfactualError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class CounterfactualService:
    def __init__(self) -> None:
        self.workspace = InvestigationWorkspaceService()

    def execute(self, db: Session, tenant_id: UUID, investigation_id: UUID, request: CounterfactualRequest) -> Scenario:
        if request.intervention_type not in SUPPORTED_INTERVENTIONS:
            raise CounterfactualError("UNSUPPORTED_INTERVENTION", "Intervention type is not supported by the constrained engine")
        investigation = db.query(Investigation).filter(Investigation.tenant_id == tenant_id, Investigation.id == investigation_id).first()
        if investigation is None:
            raise CounterfactualError("INVESTIGATION_NOT_FOUND", "Investigation is not available for this tenant")
        if request.temporal_mode == "current" and request.as_of is not None:
            raise CounterfactualError("INVALID_TEMPORAL_CONTEXT", "Current context cannot include an as-of date")
        if request.temporal_mode != "current" and request.as_of is None:
            raise CounterfactualError("INVALID_TEMPORAL_CONTEXT", "Event and Known contexts require an as-of date")
        baseline = self.workspace.workspace(db, InvestigationWorkspaceRequest(
            tenant_id=tenant_id, investigation_id=investigation_id, temporal_mode=request.temporal_mode,
            as_of=request.as_of, include_retrieval=True, retrieval_top_k=8,
        )).model_dump(mode="json")
        target = request.intervention_target.casefold()
        labels = self._labels(baseline)
        if not any(target in label.casefold() for label in labels):
            raise CounterfactualError("TARGET_NOT_FOUND", "Intervention target is not present in the selected investigation context")
        evidence_count = len(baseline.get("evidence_context", []))
        limitations = list(baseline.get("limitations", []))
        chain_exists = bool(baseline.get("relationship_context", {}).get("relationships"))
        result = {
            "classification": "COUNTERFACTUAL_RESULT",
            "status": "INSUFFICIENT_EVIDENCE" if not evidence_count else "SUCCESS",
            "label": "COUNTERFACTUAL / WHAT-IF — NOT OBSERVED EVIDENCE",
            "baseline_summary": {"investigation": baseline["investigation"], "temporal_context": baseline["temporal_context"], "evidence_count": evidence_count},
            "intervention": {"type": request.intervention_type, "target": request.intervention_target, "description": request.intervention_description},
            "invariants": ["Observed complaints and historical evidence remain observed facts.", "Canonical Product, Investigation, Evidence, and Reality Graph records are unchanged."],
            "affected_relationships": ["Relationships involving the intervention target require re-evaluation; graph adjacency is not causality."],
            "relationships_no_longer_supported": ["Candidate links through the intervention target are weakened in the derived context."] if chain_exists else [],
            "observations_still_explained": [],
            "observations_no_longer_explained": [],
            "observations_still_unexplained": ["The available evidence does not establish what would have happened under the alternative condition."],
            "hypothesis_impacts": [{"statement": "The intervention may weaken the selected explanation; it does not promote another hypothesis."}],
            "failure_chain_impact": {"status": "INCOMPLETE" if chain_exists else "NO_SUPPORTABLE_COUNTERFACTUAL", "causality_claim": False},
            "challenger_constraints": ["Challenger findings remain constraints and are not discarded."],
            "material_unknowns": ["Comparative evidence for the alternative condition is unavailable."],
            "expected_differences": [{"classification": "HYPOTHETICAL_EXPECTATION", "statement": "The candidate explanation could differ where it depends on the intervention target."}],
            "limitations": limitations + ["This is a derived reasoning exercise, not alternate history, prediction, proof, or root cause."],
            "additional_evidence_needed": ["Comparative evidence under the alternative condition and resolved traceability."],
            "conclusion": "The intervention weakens the current explanation, but available evidence is insufficient to determine the alternative outcome.",
            "provenance": {"ground_truth_used": False, "source": "investigation workspace", "derived": True, "temporal_mode": request.temporal_mode},
        }
        execution = AIExecution(tenant_id=tenant_id, investigation_id=investigation_id, requestor_ref="CONTROLLED_COUNTERFACTUAL", provider="deterministic-r1", model_name="constrained-counterfactual", model_version="day16", prompt_template_version="D16-1", orchestration_version="D16-1", context_refs={"investigation_id": str(investigation_id), "temporal_mode": request.temporal_mode}, evidence_refs={"count": evidence_count}, structured_input=request.model_dump(mode="json"), structured_output=result, rationale_summary=result["conclusion"], confidence_label="NOT_A_CONFIDENCE_SCORE", validation_status="VALIDATED")
        db.add(execution)
        scenario = Scenario(tenant_id=tenant_id, investigation_id=investigation_id, scenario_identifier=f"CF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}", question=request.intervention_description, assumptions={"kind": "COUNTERFACTUAL", "DERIVED": True, "NON_OBSERVED": True, "request": request.model_dump(mode="json"), "result": result, "ai_execution_id": str(execution.id) if execution.id else None}, uncertainty=result["conclusion"], status=result["status"])
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    def list(self, db: Session, tenant_id: UUID, investigation_id: UUID) -> list[Scenario]:
        return db.query(Scenario).filter(Scenario.tenant_id == tenant_id, Scenario.investigation_id == investigation_id).filter(Scenario.assumptions["kind"].astext == "COUNTERFACTUAL").order_by(Scenario.created_at.desc()).all()

    @staticmethod
    def _labels(baseline: dict[str, Any]) -> list[str]:
        labels: list[str] = []
        for section in (baseline.get("product_context", {}).get("configuration", {}).get("components", []), baseline.get("product_context", {}).get("changes", []), baseline.get("evidence_context", [])):
            for item in section:
                labels.extend(str(value) for value in item.values() if value is not None)
        return labels
