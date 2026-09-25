# Week 4 security and testing readiness

This checklist separates repository implementation from infrastructure evidence.
It must not be used to claim production readiness without the external gates.

## Implemented in the repository

- Durable failed-login throttling and account lockout.
- Pydantic input bounds and structured error responses.
- Secret redaction from API, export, provider, and AI boundaries.
- Production/staging cookie-origin CSRF enforcement.
- CSP, frame protection, referrer, permissions, and content-type headers.
- Playwright browser evidence scenarios and Vitest frontend tests.
- Tenant-isolation, governance, audit, and secret-redaction regression tests.
- A safe k6 smoke scenario at `scripts/k6/mdarix-smoke.js`.

## Required manual or hosted evidence

- Configure Vault or AWS Secrets Manager and rotate application/provider secrets.
- Enable TLS for the reverse proxy and PostgreSQL; verify certificate validation.
- Enable encrypted database and backup storage.
- Run k6 only against an approved staging target and archive the result.
- Run OWASP ZAP in baseline/API mode against a non-production deployment and review findings.
- Capture authenticated desktop/mobile, keyboard, and screen-reader evidence.
- Configure production monitoring and alert delivery.

## Production gate

The Week 4 gate remains **CONDITIONAL** until the external evidence above is
attached to the release report. Local code and automated tests do not prove
Vault, TLS, encryption-at-rest, backups, load capacity, or production deployment.
