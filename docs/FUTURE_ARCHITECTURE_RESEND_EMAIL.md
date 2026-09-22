# Stage 2 — Email provider boundary

Email delivery is a provider port. The initial production adapter is Resend, configured only through `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_REPLY_TO`, `RESEND_WEBHOOK_SECRET`, and `MDARIX_APP_URL`. Secrets must never be logged or returned as development tokens. Inbound webhooks require signature verification, tenant/case resolution, sender and attachment safety checks, object storage, and human review before evidence promotion.
