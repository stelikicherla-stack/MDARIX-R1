from reports.service import generate_report


def test_compliance_report_payload_is_renderable_in_all_formats():
    context = {
        "audit_events": [{"action": "SIGNED_APPROVAL_CREATED", "reason": "Reviewed evidence"}],
        "signature_verification": [{"valid": True}],
        "counts": {"audit_events": 1, "signatures": 1, "valid_signatures": 1},
    }
    json_result = generate_report("AUDIT_APPROVAL", "tenant-a", context=context, output_format="JSON")
    csv_result = generate_report("AUDIT_APPROVAL", "tenant-a", context=context, output_format="CSV")
    pdf_result = generate_report("AUDIT_APPROVAL", "tenant-a", context=context, output_format="PDF")
    assert json_result["report_version"] == "1.0"
    assert json_result["context"]["counts"]["valid_signatures"] == 1
    assert csv_result["content_type"] == "text/csv" and "SIGNED_APPROVAL_CREATED" in csv_result["content"]
    assert pdf_result["content_type"] == "application/pdf" and pdf_result["content"].startswith(b"%PDF")
