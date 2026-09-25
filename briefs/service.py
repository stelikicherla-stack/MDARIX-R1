import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from backend.app.db.models.foundation import (AIExecution, AuditEvent, Decision, Evidence, Investigation,
    InvestigationBrief, Product, ProductVersion, Hypothesis, Unknown, FailureChain, Scenario)
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService, InvestigationWorkspaceError

class BriefError(ValueError):
    def __init__(self, code: str, message: str): self.code, self.message = code, message

class BriefService:
    def __init__(self): self.workspace = InvestigationWorkspaceService()

    def _investigation(self, db, tenant_id, investigation_id):
        row = db.query(Investigation).filter(Investigation.tenant_id == tenant_id, Investigation.id == investigation_id).first()
        if not row: raise BriefError("INVESTIGATION_NOT_FOUND", "Investigation is not available for this tenant")
        return row

    def _payload(self, row: InvestigationBrief) -> dict[str, Any]:
        return {"id": row.id, "investigation_id": row.investigation_id, "brief_version": row.brief_version,
                "status": row.status, "title": row.title, "temporal_mode": row.temporal_mode,
                "temporal_cutoff": row.temporal_cutoff, "human_review_state": row.human_review_state,
                "content": row.content, "provenance": row.provenance, "limitations": row.limitations,
                "created_at": row.created_at}

    def generate(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, request) -> dict[str, Any]:
        inv = self._investigation(db, tenant_id, investigation_id)
        if request.temporal_mode == "current": cutoff = None
        else:
            cutoff = request.as_of or datetime.now(timezone.utc)
        try:
            ws = self.workspace.workspace(db, InvestigationWorkspaceRequest(tenant_id=tenant_id, investigation_id=investigation_id, temporal_mode=request.temporal_mode, as_of=cutoff, include_retrieval=True))
        except InvestigationWorkspaceError as exc: raise BriefError(exc.code, exc.message) from exc
        product = db.query(Product).filter(Product.tenant_id == tenant_id, Product.id == inv.product_id).first()
        version_id = ws.product_context.get("product_version_id")
        version = db.query(ProductVersion).filter(ProductVersion.tenant_id == tenant_id, ProductVersion.id == version_id).first() if version_id else None
        evidence = db.query(Evidence).filter(Evidence.tenant_id == tenant_id, Evidence.investigation_id == investigation_id).all()
        hypotheses = db.query(Hypothesis).filter(Hypothesis.tenant_id == tenant_id, Hypothesis.investigation_id == investigation_id).all()
        unknowns = db.query(Unknown).filter(Unknown.tenant_id == tenant_id, Unknown.investigation_id == investigation_id).all()
        chains = db.query(FailureChain).filter(FailureChain.tenant_id == tenant_id, FailureChain.investigation_id == investigation_id).all()
        scenarios = db.query(Scenario).filter(Scenario.tenant_id == tenant_id, Scenario.investigation_id == investigation_id).order_by(Scenario.created_at.desc()).limit(25).all()
        decisions = db.query(Decision).filter(Decision.tenant_id == tenant_id, Decision.investigation_id == investigation_id).order_by(Decision.decision_timestamp.desc()).all()
        decision = decisions[0] if decisions else None
        version_num = (db.query(InvestigationBrief).filter(InvestigationBrief.tenant_id == tenant_id, InvestigationBrief.investigation_id == investigation_id).count() + 1)
        now = datetime.now(timezone.utc)
        limitations = ws.limitations + [{"code": "NO_ROOT_CAUSE", "severity": "info", "description": "This Brief does not establish root cause or causality."}]
        content = {
            "investigation_identity": {"investigation_id": str(inv.id), "identifier": inv.investigation_identifier, "question": inv.investigation_question, "status": inv.status, "product_id": str(product.id) if product else None, "product": product.name if product else None, "product_version_id": str(version.id) if version else None, "product_version": version.version_identifier if version else None, "temporal_mode": request.temporal_mode, "temporal_cutoff": cutoff.isoformat() if cutoff else None, "brief_version": version_num},
            "executive_summary": {"text": "This evidence-grounded Brief preserves observed context and uncertainty. It is not a root-cause conclusion.", "observed_facts": [inv.investigation_question], "derived_facts": [], "ai_interpretation": [], "uncertainty": [item["description"] for item in limitations]},
            "what_happened": {"statement": inv.investigation_question, "status": "UNDER_INVESTIGATION"},
            "temporal_reconstruction": ws.temporal_context,
            "key_evidence": [{"evidence_id": str(e.id), "identifier": e.evidence_identifier, "title": e.title, "type": e.evidence_type, "source": e.source_reference, "reliability": e.reliability_status, "fact_type": e.fact_type} for e in evidence],
            "supporting_evidence": [], "contradicting_evidence": [],
            "hypotheses": [{"id": str(h.id), "statement": h.statement, "status": h.status, "origin": h.origin} for h in hypotheses],
            "ai_challenger_findings": [], "unknowns": [{"id": str(u.id), "description": u.description, "status": u.status, "category": u.category} for u in unknowns],
            "failure_chain": [{"id": str(c.id), "name": c.name, "status": c.status} for c in chains],
            "scenario_findings": [s.assumptions.get("result", {}) for s in scenarios if isinstance(s.assumptions, dict) and s.assumptions.get("kind") == "SCENARIO"],
            "counterfactual_analysis": {"status": "NOT_INCLUDED", "label": "HYPOTHETICAL / NON-OBSERVED ANALYSIS", "message": "No persisted Counterfactual result was selected for this Brief."},
            "ai_advisory": {"label": "AI ADVISORY — HUMAN REVIEW REQUIRED", "status": "NOT_EMBEDDED", "message": "AI recommendation remains separate from this deterministic Brief."},
            "supported_conclusions": ["The investigation context and listed evidence are preserved for review."],
            "not_established": ["Causality is not established.", "Root cause is not established.", "This Brief is not an approval, recall, CAPA, vigilance decision, or automatic closure."],
            "human_decision": {"present": bool(decision), "decision_id": str(decision.id) if decision else None, "disposition": decision.disposition if decision else None, "rationale": decision.rationale if decision else None, "authorized_by_ref": decision.authorized_by_ref if decision else None, "timestamp": decision.decision_timestamp.isoformat() if decision and decision.decision_timestamp else None},
            "limitations": limitations,
        }
        from genai.grounding import advisory, build_authorized_context
        grounded = build_authorized_context(db, tenant_id=tenant_id, investigation_id=investigation_id, product_version_id=version.id if version else None, temporal_mode=request.temporal_mode, as_of=cutoff)
        content["ai_advisory"] = {"label": "AI ADVISORY — HUMAN REVIEW REQUIRED", **advisory(workflow="DECISION_BRIEF_DRAFT", deterministic_result=content, grounded_context=grounded, question=inv.investigation_question)}
        provenance = {"investigation_id": str(inv.id), "product_id": str(inv.product_id), "product_version_id": str(version.id) if version else None, "evidence_ids": [str(e.id) for e in evidence], "hypothesis_ids": [str(h.id) for h in hypotheses], "unknown_ids": [str(u.id) for u in unknowns], "failure_chain_ids": [str(c.id) for c in chains], "scenario_ids": [str(s.id) for s in scenarios], "decision_id": str(decision.id) if decision else None, "assembler": "MDARIX-Controlled-Brief-Assembler-v1", "ground_truth_references": [], "generated_at": now.isoformat()}
        row = InvestigationBrief(id=uuid.uuid4(), tenant_id=tenant_id, investigation_id=inv.id, product_id=inv.product_id, product_version_id=version.id if version else None, brief_version=version_num, status="GENERATED", title=f"Investigation Brief — {inv.investigation_identifier}", generated_by=request.generated_by, temporal_mode=request.temporal_mode, temporal_cutoff=cutoff, human_review_state="NOT_REVIEWED", decision_id=decision.id if decision else None, limitations={"items": limitations}, content=content, provenance=provenance, created_at=now, updated_at=now)
        db.add(row); db.add(AuditEvent(tenant_id=tenant_id, actor_ref=request.generated_by, action="BRIEF_GENERATED" if version_num == 1 else "BRIEF_REGENERATED", entity_type="investigation_brief", entity_id=row.id, details={"investigation_id": str(inv.id), "brief_version": version_num}, created_at=now)); db.commit(); db.refresh(row)
        return self._payload(row)

    def list(self, db, tenant_id, investigation_id):
        self._investigation(db, tenant_id, investigation_id)
        return [self._payload(x) for x in db.query(InvestigationBrief).filter(InvestigationBrief.tenant_id == tenant_id, InvestigationBrief.investigation_id == investigation_id).order_by(InvestigationBrief.brief_version.desc()).all()]

    def get(self, db, tenant_id, investigation_id, brief_id=None, latest=False):
        self._investigation(db, tenant_id, investigation_id); q = db.query(InvestigationBrief).filter(InvestigationBrief.tenant_id == tenant_id, InvestigationBrief.investigation_id == investigation_id)
        row = q.order_by(InvestigationBrief.brief_version.desc()).first() if latest else q.filter(InvestigationBrief.id == brief_id).first()
        if not row: raise BriefError("BRIEF_NOT_FOUND", "Investigation Brief is not available for this tenant")
        return self._payload(row)
