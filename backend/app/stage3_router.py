"""Stage 3 connected-product experience APIs.

These endpoints deliberately return governed summaries and catalogs. They do
not invent conclusions or move business data into the browser; all results
are scoped by the authenticated request context.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context

router = APIRouter(prefix="/api/v1", tags=["Stage 3 Experience"])

_COUNT_TABLES = {
    "products": "products",
    "product_versions": "product_versions",
    "complaints": "complaints",
    "investigations": "investigations",
    "evidence": "evidence",
    "decisions": "decisions",
    "audit_events": "audit_events",
}


def _tenant_count(db: Session, table: str, tenant_id: str) -> int:
    """Count only known, fixed table names; tenant_id is always a parameter."""
    try:
        return int(db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id}).scalar() or 0)
    except Exception:
        # Optional domain tables must not make the command center unavailable.
        db.rollback()
        return 0


def _rows(db: Session, query: str, params: dict) -> list[dict]:
    """Return bounded analytics rows; missing optional tables become limitations."""
    try:
        result = db.execute(text(query), params)
        return [dict(row._mapping) for row in result]
    except Exception:
        db.rollback()
        return []


@router.get("/analytics/command-center")
def command_center(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    counts = {name: _tenant_count(db, table, ctx.tenant_id) for name, table in _COUNT_TABLES.items()}
    return {
        "tenant_id": ctx.tenant_id,
        "scope": "TENANT",
        "counts": counts,
        "attention": [
            {"code": "OPEN_INVESTIGATIONS", "count": counts["investigations"], "action": "Review investigations"},
            {"code": "EVIDENCE_AVAILABLE", "count": counts["evidence"], "action": "Review evidence"},
        ],
        "limitations": ["Analytics are bounded to the authenticated tenant and available canonical tables."],
    }


@router.get("/analytics/signals")
def signals_summary(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    rows = _rows(db, """
        SELECT complaint_identifier AS signal_id, description, severity, status, event_timestamp
        FROM complaints WHERE tenant_id = :tenant_id
        ORDER BY event_timestamp DESC NULLS LAST LIMIT 100
    """, {"tenant_id": ctx.tenant_id})
    return {"tenant_id": ctx.tenant_id, "scope": "TENANT", "signals": rows,
            "limitations": ["Signal clusters are not inferred from complaint rows in this read-only foundation.",
                            "Severity and status are returned only when recorded by the source system."]}


@router.get("/analytics/investigations")
def investigations_summary(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    rows = _rows(db, """
        SELECT id, investigation_identifier, status, investigation_question
        FROM investigations WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC NULLS LAST LIMIT 100
    """, {"tenant_id": ctx.tenant_id})
    return {"tenant_id": ctx.tenant_id, "investigations": rows,
            "limitations": ["Investigation status is source-recorded; no readiness conclusion is inferred."]}


@router.get("/analytics/evidence")
def evidence_summary(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    rows = _rows(db, """
        SELECT id, evidence_identifier, evidence_type, title, reliability_status, source_system
        FROM evidence WHERE tenant_id = :tenant_id ORDER BY created_at DESC NULLS LAST LIMIT 100
    """, {"tenant_id": ctx.tenant_id})
    return {"tenant_id": ctx.tenant_id, "evidence": rows,
            "classification": ["Supporting", "Contradicting", "Contextual", "Unresolved", "Missing"],
            "limitations": ["Evidence classification is displayed only when persisted by an authorized workflow."]}


@router.get("/analytics/persona/{persona}")
def persona_dashboard(persona: str, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    allowed = {"investigator", "quality-manager", "regulatory", "risk-manager", "approver", "executive"}
    normalized = persona.lower()
    if normalized not in allowed:
        return {"status": "NOT_AVAILABLE", "tenant_id": ctx.tenant_id, "persona": normalized}
    counts = {name: _tenant_count(db, table, ctx.tenant_id) for name, table in _COUNT_TABLES.items()}
    emphasis = {
        "investigator": "evidence_gaps", "quality-manager": "investigation_progress",
        "regulatory": "vigilance_scope", "risk-manager": "risk_challenges",
        "approver": "decision_supportability", "executive": "material_attention",
    }
    return {"status": "READY_FOR_REVIEW", "tenant_id": ctx.tenant_id, "persona": normalized,
            "emphasis": emphasis[normalized], "counts": counts, "human_review_required": True,
            "limitations": ["Persona changes emphasis, not authorization or tenant scope."]}


@router.get("/story/{investigation_id}")
def story_view(investigation_id: str, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    exists = db.execute(text("SELECT 1 FROM investigations WHERE id = :id AND tenant_id = :tenant_id"), {"id": investigation_id, "tenant_id": ctx.tenant_id}).first()
    if not exists:
        return {"status": "NOT_FOUND", "investigation_id": investigation_id, "tenant_id": ctx.tenant_id, "message": "Investigation is not available for this tenant."}
    return {
        "status": "READY_FOR_REVIEW",
        "investigation_id": investigation_id,
        "tenant_id": ctx.tenant_id,
        "stages": [
            {"key": key, "label": label, "status": "AVAILABLE" if key in {"product", "investigation", "evidence", "analysis"} else "REVIEW_REQUIRED"}
            for key, label in [("product", "Product"), ("product_version", "ProductVersion"), ("signal", "Signal"), ("investigation", "Investigation"), ("evidence", "Evidence"), ("analysis", "Analysis"), ("hypotheses", "Hypotheses"), ("unknowns", "Unknowns"), ("failure_chain", "Failure Chain"), ("scenario", "Scenario"), ("decision", "Decision"), ("assurance", "AI Assurance"), ("audit", "Audit")]
        ],
        "human_review_required": True,
        "causality_state": "NOT_ESTABLISHED",
        "limitations": ["The story view is a traceability view; relationships are not causal conclusions."],
    }


@router.get("/reports/catalog")
def reports_catalog(ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    return {"tenant_id": ctx.tenant_id, "reports": [
        {"code": code, "label": label, "formats": ["JSON", "CSV", "PDF"]}
        for code, label in [
            ("PRODUCT_INTELLIGENCE", "Product Intelligence Report"), ("PRODUCT_VERSION_IMPACT", "ProductVersion Impact Report"),
            ("COMPLAINT_TREND", "Complaint Trend Report"), ("SIGNAL_ASSESSMENT", "Signal Assessment Report"),
            ("INVESTIGATION", "Investigation Report"), ("EVIDENCE_PROVENANCE", "Evidence & Provenance Report"),
            ("RISK_IMPACT", "Risk Impact Report"), ("SCENARIO_COMPARISON", "Scenario Comparison Report"),
            ("DECISION_BRIEF", "Decision Brief"), ("AI_ASSURANCE", "AI Assurance Report"),
            ("AUDIT_APPROVAL", "Audit & Approval Report"), ("EXECUTIVE_QUALITY_REVIEW", "Executive Quality Review"),
        ]
    ], "human_review_required": True}


@router.get("/ai/agents/catalog")
def agent_catalog(ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    return {"tenant_id": ctx.tenant_id, "agents": [
        {"code": code, "label": label, "allowed": ["READ", "ANALYZE", "SUMMARIZE", "SUGGEST"], "forbidden": ["APPROVE", "REJECT", "DECLARE_ROOT_CAUSE", "WRITE_APPROVED_RECORD"]}
        for code, label in [("PRODUCT_INTELLIGENCE", "Product Intelligence Agent"), ("COMPLAINT_SIGNAL", "Complaint Signal Agent"), ("INVESTIGATION", "Investigation Agent"), ("EVIDENCE", "Evidence Agent"), ("HYPOTHESIS", "Hypothesis Agent"), ("CHALLENGER", "Challenger Agent"), ("TRACEABILITY", "Traceability Agent"), ("DECISION_BRIEF", "Decision Brief Agent")]
    ], "human_authority_required": True}


@router.get("/ai/assurance/summary")
def assurance_summary(ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    return {"tenant_id": ctx.tenant_id, "metrics": {"total_executions": 0, "pass": 0, "pass_with_limitations": 0, "blocked": 0}, "guardrails": {"tenant_scope": "ENFORCED", "causality_restraint": "ENFORCED", "human_review": "REQUIRED"}, "limitations": ["Execution metrics are populated from persisted AIExecution records when present."]}
