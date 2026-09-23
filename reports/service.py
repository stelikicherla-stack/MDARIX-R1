from datetime import datetime, timezone

REPORTS = {"PRODUCT_INTELLIGENCE":"Product Intelligence Report","COMPLAINT_TREND":"Complaint Trend Report","SIGNAL_ASSESSMENT":"Signal Assessment Report","INVESTIGATION":"Investigation Report","EVIDENCE_PROVENANCE":"Evidence & Provenance Report","DECISION_BRIEF":"Decision Brief","AI_ASSURANCE":"AI Assurance Report","AUDIT_APPROVAL":"Audit & Approval Report"}

def generate_report(code: str, tenant_id: str, *, context: dict | None = None) -> dict:
    if code not in REPORTS: raise ValueError("REPORT_TYPE_NOT_SUPPORTED")
    return {"report_type": code, "title": REPORTS[code], "tenant_id": tenant_id, "status": "READY_FOR_REVIEW", "generated_at": datetime.now(timezone.utc).isoformat(), "context": context or {}, "limitations": ["Report is a governed summary; it does not establish causality or replace human approval."], "human_review_required": True}
