# Resend Communication Architecture

MDARIX uses the provider-neutral `EmailProvider` boundary. Resend is an optional production provider configured by `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_REPLY_TO`, `RESEND_WEBHOOK_SECRET`, and `MDARIX_APP_URL`. Secrets are server-side only. SMTP remains a fallback and is not the primary application provider.

Outbound templates are versionable and categorized as TRANSACTIONAL or REGULATED_WORKFLOW. Delivery failures are controlled and must not expose provider secrets.
