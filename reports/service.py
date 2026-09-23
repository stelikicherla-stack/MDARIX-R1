from datetime import datetime, timezone
import csv, io

REPORTS = {"PRODUCT_INTELLIGENCE":"Product Intelligence Report","COMPLAINT_TREND":"Complaint Trend Report","SIGNAL_ASSESSMENT":"Signal Assessment Report","INVESTIGATION":"Investigation Report","EVIDENCE_PROVENANCE":"Evidence & Provenance Report","DECISION_BRIEF":"Decision Brief","AI_ASSURANCE":"AI Assurance Report","AUDIT_APPROVAL":"Audit & Approval Report"}

def generate_report(code: str, tenant_id: str, *, context: dict | None = None, output_format: str = "JSON") -> dict:
    if code not in REPORTS: raise ValueError("REPORT_TYPE_NOT_SUPPORTED")
    fmt = output_format.upper()
    if fmt not in {"JSON", "CSV", "PDF"}: raise ValueError("REPORT_FORMAT_NOT_SUPPORTED")
    generated = datetime.now(timezone.utc).isoformat(); data = {"report_type": code, "title": REPORTS[code], "tenant_id": tenant_id, "status": "READY_FOR_REVIEW", "generated_at": generated, "context": context or {}, "limitations": ["Report is a governed summary; it does not establish causality or replace human approval."], "human_review_required": True}
    if fmt == "CSV":
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(["field", "value"]); [writer.writerow([key, str(value)]) for key, value in data.items()]; data["content_type"] = "text/csv"; data["content"] = out.getvalue()
    elif fmt == "PDF":
        text = f"MDARIX {REPORTS[code]} | tenant={tenant_id} | status=READY_FOR_REVIEW"
        stream = f"BT /F1 10 Tf 40 760 Td ({text.replace('(', '[').replace(')', ']')}) Tj ET"; pdf = f"%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1>>endobj\n3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources<< /Font<< /F1 4 0 R>>>> /Contents 5 0 R>>endobj\n4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj\n5 0 obj<< /Length {len(stream.encode())}>>stream\n{stream}\nendstream endobj\ntrailer<< /Root 1 0 R>>\n%%EOF"; data["content_type"] = "application/pdf"; data["content"] = pdf.encode("latin-1").hex()
    data["format"] = fmt; return data
