"""Stage 3 connected-product experience APIs.

These endpoints deliberately return governed summaries and catalogs. They do
not invent conclusions or move business data into the browser; all results
are scoped by the authenticated request context.
"""
from fastapi import APIRouter, Depends, Query
from decimal import Decimal, InvalidOperation
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from backend.app.db.models.foundation import AIExecution

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

def _execution_cost(row: AIExecution) -> Decimal:
    payload = row.structured_output or {}
    audit = payload.get("audit", {}) if isinstance(payload, dict) else {}
    if isinstance(payload, dict) and isinstance(payload.get("provenance"), dict):
        audit = payload["provenance"].get("audit", audit)
    try: return Decimal(str(audit.get("estimated_cost", 0)))
    except (InvalidOperation, TypeError): return Decimal("0")

@router.get("/analytics/ai/provider-monitoring")
def ai_provider_monitoring(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    """Tenant-scoped operational view for provider health and persisted executions."""
    rows = db.query(AIExecution).filter(AIExecution.tenant_id == ctx.tenant_id).order_by(AIExecution.execution_timestamp.desc()).limit(1000).all()
    failures = [row for row in rows if row.error_state or str(row.validation_status or "").upper() in {"FAILED", "BLOCKED"}]
    latencies = [row.latency_ms for row in rows if row.latency_ms is not None]
    by_provider = {}
    for row in rows:
        item = by_provider.setdefault(row.provider, {"executions": 0, "failures": 0, "estimated_cost": Decimal("0")})
        item["executions"] += 1; item["failures"] += int(row in failures); item["estimated_cost"] += _execution_cost(row)
    return {"tenant_id": ctx.tenant_id, "status": "DEGRADED" if failures else "HEALTHY", "metrics": {"executions": len(rows), "failures": len(failures), "failure_rate": round(len(failures) / len(rows), 4) if rows else 0, "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * .95) - 1)] if latencies else None}, "providers": [{**item, "estimated_cost": str(item["estimated_cost"])} for item in ({"provider": key, **value} for key, value in by_provider.items())], "alert": bool(failures), "limitations": ["Metrics are tenant-scoped persisted execution telemetry; external provider monitoring remains deployment-specific."]}

@router.get("/analytics/ai/cost-reconciliation")
def ai_cost_reconciliation(provider_invoice_total: str | None = Query(default=None), db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    """Reconcile persisted estimated provider cost with an supplied invoice total."""
    rows = db.query(AIExecution).filter(AIExecution.tenant_id == ctx.tenant_id).limit(10000).all()
    estimated = sum((_execution_cost(row) for row in rows), Decimal("0"))
    invoice = None
    variance = None
    if provider_invoice_total is not None:
        try:
            invoice = Decimal(provider_invoice_total); variance = invoice - estimated
        except InvalidOperation: return {"code": "INVALID_INVOICE_TOTAL", "message": "provider_invoice_total must be a decimal amount"}
    return {"tenant_id": ctx.tenant_id, "currency": "USD", "execution_count": len(rows), "estimated_total": str(estimated), "provider_invoice_total": str(invoice) if invoice is not None else None, "variance": str(variance) if variance is not None else None, "within_tolerance": abs(variance) <= Decimal("0.01") if variance is not None else None, "status": "REQUIRES_PROVIDER_INVOICE" if invoice is None else ("RECONCILED" if abs(variance) <= Decimal("0.01") else "VARIANCE_REQUIRES_REVIEW"), "human_review_required": True}
