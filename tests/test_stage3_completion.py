from reports.service import generate_report, submit_report_job, get_report_job
from communication.email.resend_provider import ResendProvider
from object_storage.service import ObjectStorageService

def test_report_service_is_tenant_scoped():
    result = generate_report("DECISION_BRIEF", "tenant-a")
    assert result["tenant_id"] == "tenant-a" and result["human_review_required"]

def test_resend_provider_safe_unconfigured_health(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False); monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    result = ResendProvider().health(); assert result["configured"] is False and "api_key_present" in result

def test_object_storage_returns_provenance(tmp_path):
    result = ObjectStorageService(str(tmp_path)).put("tenant-a", "mail/file.txt", b"evidence")
    assert result["tenant_id"] == "tenant-a" and result["size"] == 8 and result["checksum"]
    assert ObjectStorageService(str(tmp_path)).get("tenant-a", result["object_key"]) == b"evidence"

def test_object_storage_is_tenant_scoped_and_can_sign_local_urls(tmp_path, monkeypatch):
    monkeypatch.setenv("MDARIX_OBJECT_STORAGE_SIGNING_SECRET", "test-secret")
    storage = ObjectStorageService(str(tmp_path))
    result = storage.put("tenant-a", "evidence/file.txt", b"evidence")
    assert "tenant-a/" in result["object_key"]
    assert "signature=" in storage.signed_url("tenant-a", result["object_key"])
    signed = storage.signed_url("tenant-a", result["object_key"])
    assert storage.verify_signed_url("tenant-a", signed) == result["object_key"]
    try:
        storage.get("tenant-b", result["object_key"])
        assert False, "foreign tenant read must fail"
    except FileNotFoundError:
        pass

def test_object_storage_enforces_object_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("MDARIX_OBJECT_STORAGE_MAX_BYTES", "3")
    storage = ObjectStorageService(str(tmp_path))
    try:
        storage.put("tenant-a", "too-large.bin", b"1234")
        assert False, "oversized object must be rejected"
    except RuntimeError as exc:
        assert str(exc) == "OBJECT_SIZE_QUOTA_EXCEEDED"

def test_report_renderer_supports_csv_and_pdf():
    csv_result = generate_report("DECISION_BRIEF", "tenant-a", output_format="CSV")
    pdf_result = generate_report("DECISION_BRIEF", "tenant-a", output_format="PDF")
    assert csv_result["content_type"] == "text/csv" and "report_type" in csv_result["content"]
    assert pdf_result["content_type"] == "application/pdf" and pdf_result["content"]

def test_report_job_is_tenant_scoped_and_versioned(tmp_path, monkeypatch):
    monkeypatch.setenv("MDARIX_REPORT_TEMP_ROOT", str(tmp_path))
    job = submit_report_job("DECISION_BRIEF", "tenant-a", actor_id="user-a", output_format="PDF")
    assert job["status"] == "READY" and job["report_version"] == "1.0"
    assert get_report_job(job["id"], "tenant-a")["path"].startswith(str(tmp_path))
    try:
        get_report_job(job["id"], "tenant-b")
        assert False, "foreign tenant must not access report job"
    except ValueError as exc:
        assert str(exc) == "REPORT_JOB_NOT_FOUND"
