# Inbound Email Evidence Workflow

Resend `email.received` events must pass signature verification, event validation, deduplication, tenant/case routing, sender validation, and attachment security checks. The resulting item remains `PENDING_HUMAN_REVIEW`; received email or attachments never become trusted evidence automatically. Original message and attachment provenance must be retained through the object-storage abstraction.
