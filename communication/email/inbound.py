import hashlib
import hmac
import os


def verify_webhook(payload: bytes, signature: str | None, secret: str | None = None) -> bool:
    configured = secret or os.getenv("RESEND_WEBHOOK_SECRET")
    if not configured or not signature:
        return False
    expected = hmac.new(configured.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def classify_inbound_event(event: dict) -> dict:
    event_type = event.get("type")
    if event_type in {"email.bounced", "email.complained"}:
        return {"status": "DELIVERY_FAILURE_REVIEW", "processing_state": "BOUNCE_RECORDED", "trusted_provider_event_id": event.get("id"), "evidence_acceptance": "NEVER_AUTOMATIC"}
    if event_type != "email.received":
        return {"status": "REJECTED", "reason": "UNSUPPORTED_EVENT_TYPE"}
    return {"status": "PENDING_HUMAN_REVIEW", "processing_state": "RECEIVED", "trusted_provider_event_id": event.get("id"), "evidence_acceptance": "NEVER_AUTOMATIC"}
