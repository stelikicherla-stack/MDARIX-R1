import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.db.models.foundation import AuditEvent, Decision, HumanReview, AIExecution, Investigation
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService, InvestigationWorkspaceError
from decision_center.schemas import AdvisoryRequest, DecisionContextRequest, DecisionCreateRequest, ReviewCreateRequest

OPTIONS = [
    "CONTINUE_INVESTIGATION", "REQUEST_ADDITIONAL_EVIDENCE", "REQUEST_ADDITIONAL_TESTING",
    "REVIEW_SUPPLIER_CHANGE", "REVIEW_PRODUCT_CHANGE", "ESCALATE_FOR_QUALITY_REVIEW",
    "ESCALATE_FOR_REGULATORY_REVIEW", "ESCALATE_FOR_RISK_REVIEW", "NO_DECISION_YET",
]


class DecisionCenterError(ValueError):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


class DecisionCenterService:
    def __init__(self) -> None:
        self.workspace_service = InvestigationWorkspaceService()

    def _investigation(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> Investigation:
        row = db.query(Investigation).filter(Investigation.tenant_id == tenant_id, Investigation.id == investigation_id).first()
        if not row:
            raise DecisionCenterError("INVESTIGATION_NOT_FOUND", "Investigation is not available for this tenant")
        return row

    def _latest(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, orchestration: str) -> dict[str, Any] | None:
        row = db.query(AIExecution).filter(
            AIExecution.tenant_id == tenant_id,
            AIExecution.investigation_id == investigation_id,
            AIExecution.orchestration_version == orchestration,
        ).order_by(AIExecution.execution_timestamp.desc()).first()
        if not row:
            return None
        return {"execution_id": str(row.id), "output": row.structured_output or {}, "context_refs": row.context_refs or {}, "evidence_refs": row.evidence_refs or {}}

    def context(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, request: DecisionContextRequest) -> dict[str, Any]:
        investigation = self._investigation(db, tenant_id, investigation_id)
        try:
            workspace = self.workspace_service.workspace(db, InvestigationWorkspaceRequest(
                tenant_id=tenant_id, investigation_id=investigation_id, temporal_mode=request.temporal_mode,
                as_of=request.as_of, include_retrieval=True, retrieval_top_k=8,
            ))
        except InvestigationWorkspaceError as exc:
            raise DecisionCenterError(exc.code, exc.message) from exc
        analysis = self._latest(db, tenant_id, investigation_id, "R1-Day11")
        hypotheses = self._latest(db, tenant_id, investigation_id, "R1-Day12")
        challenges = self._latest(db, tenant_id, investigation_id, "R1-Day13")
        unknowns = self._latest(db, tenant_id, investigation_id, "R1-Day14-Unknowns")
        chains = self._latest(db, tenant_id, investigation_id, "R1-Day14-FailureChain")
        observations = (analysis or {}).get("output", {}).get("observations", [])
        contradictions = (analysis or {}).get("output", {}).get("contradictions", [])
        hypothesis_items = (hypotheses or {}).get("output", {}).get("hypotheses", [])
        challenge_items = (challenges or {}).get("output", {}).get("challenges", [])
        unknown_items = (unknowns or {}).get("output", {}).get("unknowns", [])
        chain_items = (chains or {}).get("output", {}).get("chains", [])
        limitations = list(workspace.limitations)
        if not workspace.evidence_context:
            limitations.append({"code": "NO_INVESTIGATION_EVIDENCE", "severity": "MATERIAL", "description": "No evidence is available in this investigation context."})
        reasons = []
        if not observations: reasons.append("No persisted AI Investigator observations are available.")
        if not hypothesis_items: reasons.append("No persisted competing hypotheses are available.")
        if contradictions or challenge_items: reasons.append("Contradictions or Challenger findings require human review.")
        if any(item.get("materiality") == "MATERIAL" for item in unknown_items): reasons.append("Material unknowns remain unresolved.")
        if not chain_items or any(item.get("overall_status") in {"BROKEN_CHAIN", "ABSTAINED"} for item in chain_items): reasons.append("The failure chain is incomplete or not supportable.")
        readiness = "SUFFICIENT_FOR_REVIEW" if not reasons else ("CONTRADICTORY_EVIDENCE" if contradictions or challenge_items else "MATERIAL_UNKNOWNS_REMAIN")
        if not workspace.evidence_context and not observations: readiness = "INSUFFICIENT_EVIDENCE"
        selected_version = workspace.product_context.get("selected_version") or {}
        product = workspace.product_context.get("product") or {}
        return {
            "investigation": {"id": str(investigation.id), "identifier": investigation.investigation_identifier, "question": investigation.investigation_question, "status": investigation.status},
            "product_context": {**workspace.product_context, "product_id": product.get("id") or str(investigation.product_id), "product_version_id": selected_version.get("id"), "product": product, "selected_version": selected_version}, "temporal_context": workspace.temporal_context,
            "evidence": [item if isinstance(item, dict) else item.model_dump(mode="json") for item in workspace.evidence_context],
            "observations": observations, "contradictions": contradictions, "hypotheses": hypothesis_items,
            "challenges": challenge_items, "unknowns": unknown_items, "failure_chains": chain_items,
            "limitations": limitations, "readiness": {"state": readiness, "reasons": reasons},
            "decision_options": OPTIONS, "provenance": {"analysis": analysis, "hypotheses": hypotheses, "challenges": challenges, "unknowns": unknowns, "failure_chains": chains},
            "guardrails": {"human_decision_required": True, "ai_advisory_is_not_decision": True, "ground_truth_used": False, "tenant_id": str(tenant_id)},
        }

    def advisory(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, request: AdvisoryRequest) -> dict[str, Any]:
        context = self.context(db, tenant_id, investigation_id, request)
        recommendation = "NO_DECISION_YET" if context["readiness"]["state"] in {"INSUFFICIENT_EVIDENCE", "MATERIAL_UNKNOWNS_REMAIN", "CONTRADICTORY_EVIDENCE"} else "READY_FOR_HUMAN_DECISION"
        output = {"investigation_id": str(investigation_id), "decision_question": request.decision_question, "current_state": context["readiness"], "recommended_action": recommendation, "decision_options": context["decision_options"], "additional_evidence_needed": context["readiness"]["reasons"], "limitations": context["limitations"], "provenance": context["provenance"], "human_authority_required": True}
        from genai.grounding import advisory as grounded_advisory, build_authorized_context
        grounded = build_authorized_context(
            db, tenant_id=tenant_id, investigation_id=investigation_id,
            product_version_id=context["product_context"].get("product_version_id"),
            temporal_mode=request.temporal_mode, as_of=request.as_of,
        )
        output["ai_advisory"] = grounded_advisory(
            workflow="DECISION_CENTER_ADVISORY", deterministic_result=output,
            grounded_context=grounded, question=request.decision_question,
        )
        row = AIExecution(id=uuid.uuid4(), tenant_id=tenant_id, investigation_id=investigation_id, provider="mdarix-controlled-decision-advisory", model_name="mdarix-rule-grounded-advisory", model_version="1.0", prompt_template_version="R1-Day15-DecisionAdvisory-v1", orchestration_version="R1-Day15-DecisionAdvisory", context_refs={"temporal_context": context["temporal_context"]}, evidence_refs={"evidence_identifiers": [item.get("evidence_identifier") for item in context["evidence"]]}, structured_input=request.model_dump(mode="json"), structured_output=output, validation_status="COMPLETED", execution_timestamp=datetime.now(timezone.utc), requestor_ref="MDARIX-Decision-Center")
        db.add(row); db.add(AuditEvent(tenant_id=tenant_id, actor_ref="MDARIX-Decision-Center", action="DECISION_ADVISORY_CREATED", entity_type="investigation", entity_id=investigation_id, details={"ai_execution_id": str(row.id), "temporal_context": context["temporal_context"]}, created_at=datetime.now(timezone.utc))); db.commit()
        return {"advisory": output, "ai_execution_id": row.id, "context": context}

    def create_decision(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, request: DecisionCreateRequest) -> Decision:
        context = self.context(db, tenant_id, investigation_id, request)
        identifier = f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(investigation_id)[:8]}"
        row = Decision(id=uuid.uuid4(), tenant_id=tenant_id, investigation_id=investigation_id, decision_identifier=identifier, decision_type=request.decision_type, disposition=request.selected_action, rationale=request.rationale, decision_timestamp=datetime.now(timezone.utc), authorized_by_ref=request.authorized_by_ref, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc), product_id=context["product_context"].get("product_id"), product_version_id=context["product_context"].get("product_version_id"), decision_status="REQUIRES_REVIEW", decision_readiness=context["readiness"]["state"], selected_action=request.selected_action, temporal_context=context["temporal_context"], limitations={"items": context["limitations"]}, context_snapshot={"readiness": context["readiness"], "hypotheses": context["hypotheses"], "unknowns": context["unknowns"], "failure_chains": context["failure_chains"]})
        db.add(row); db.add(AuditEvent(tenant_id=tenant_id, actor_ref=request.authorized_by_ref, action="DECISION_CREATED", entity_type="decision", entity_id=row.id, details={"investigation_id": str(investigation_id), "decision_status": row.decision_status}, created_at=datetime.now(timezone.utc))); db.commit(); db.refresh(row); return row

    def review(self, db: Session, tenant_id: uuid.UUID, decision_id: uuid.UUID, request: ReviewCreateRequest) -> HumanReview:
        decision = db.query(Decision).filter(Decision.tenant_id == tenant_id, Decision.id == decision_id).first()
        if not decision: raise DecisionCenterError("DECISION_NOT_FOUND", "Decision is not available for this tenant")
        review = HumanReview(id=uuid.uuid4(), tenant_id=tenant_id, investigation_id=decision.investigation_id, decision_id=decision.id, reviewer_ref=request.reviewer_ref, disposition=request.disposition, comments=request.comments, review_timestamp=datetime.now(timezone.utc))
        decision.decision_status = "DECIDED" if request.disposition == "APPROVED" else "REQUIRES_ADDITIONAL_EVIDENCE"; decision.updated_at = datetime.now(timezone.utc); db.add(review); db.add(AuditEvent(tenant_id=tenant_id, actor_ref=request.reviewer_ref, action="DECISION_REVIEWED", entity_type="decision", entity_id=decision.id, details={"disposition": request.disposition, "comments": request.comments}, created_at=datetime.now(timezone.utc))); db.commit(); db.refresh(review); return review
