import hashlib
import hmac

from communication.email.inbound import classify_inbound_event, verify_webhook
from communication.email.resend_provider import ResendProvider


def test_resend_health_never_exposes_secret(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "secret-value")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "sender@example.test")
    result = ResendProvider().health()
    assert result["configured"] is True
    assert "secret-value" not in str(result)


def test_webhook_signature_and_manual_review_gate():
    body = b'{"id":"evt-1","type":"email.received"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert verify_webhook(body, signature, "secret") is True
    assert classify_inbound_event({"id": "evt-1", "type": "email.received"})["status"] == "PENDING_HUMAN_REVIEW"
    assert classify_inbound_event({"id": "evt-2", "type": "email.sent"})["status"] == "REJECTED"

def test_sender_domain_is_verified_before_resend_delivery(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "secret-value")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "sender@example.test")
    monkeypatch.setenv("RESEND_VERIFIED_DOMAIN", "verified.example")
    result = ResendProvider().health()
    assert result["configured"] is False
    assert result["sender_domain_verified"] is False

def test_bounce_is_a_persistable_review_state():
    result = classify_inbound_event({"id": "evt-bounce", "type": "email.bounced"})
    assert result["status"] == "DELIVERY_FAILURE_REVIEW"
    assert result["processing_state"] == "BOUNCE_RECORDED"
