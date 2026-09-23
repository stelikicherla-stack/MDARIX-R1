from reports.service import generate_report
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
