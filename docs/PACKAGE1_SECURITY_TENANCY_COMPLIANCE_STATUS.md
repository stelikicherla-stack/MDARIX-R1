# Package 1 — Security, Tenancy, and Compliance Status

Date: 2026-09-26

## Automated validation

The focused Package 1 suite passed:

```text
31 passed, 1 warning
```

Covered areas include request-context authentication, deny-by-default access,
governance and SoD, CSRF/security behavior, secret redaction, field-filtered
exports and AI context, audit immutability, compliance reports, and signature
verification.

## Completed or implemented

- Authenticated request context binds tenant and user server-side.
- Cross-tenant access is denied by tenant-scoped service/query checks.
- Hidden and protected fields are excluded from exports and AI context.
- Cookie-authenticated production state changes require a trusted origin.
- Durable failed-login throttling and account lockout are present.
- Audit events capture correlation and request metadata through the shared audit
  helper and mutation envelope.
- Audit immutability migration protects audit events from update/delete.
- Governance checks include entitlement, approval authority, SoD, re-authentication,
  object-version binding, remarks, and signature fingerprint verification.
- Compliance audit/signature reports support JSON, CSV, and PDF generation.
- Production-like two-instance session reuse and cross-instance revocation passed
  through `scripts/verify_stage2_multi_instance.py`.

## Remaining Package 1 gates

### Requires implementation or explicit policy decision

- Full MFA enrollment/challenge/recovery ceremony. Signature enforcement can
  require MFA through `MDARIX_REQUIRE_MFA_FOR_SIGNATURES`, but the complete MFA
  identity flow still needs a durable provider or IdP integration.
- Standardized old-value/new-value capture for every domain mutation, rather
  than only the routes that already provide structured diffs.
- Formal seven-year audit retention configuration and retention monitoring.
- Complete browser evidence for admin, customer admin, exports, and approvals.

### Requires production infrastructure

- Runtime switch to the approved non-superuser database role.
- PostgreSQL TLS and encrypted backup/WAL storage.
- Backup, restore, and PITR rehearsal.
- Production monitoring and alert destination.
- Full ZAP/manual penetration assessment.
- Hosted CI execution and retained scan artifacts.

## Package 1 conclusion

Package 1 application controls are **substantially implemented and focused
tests pass**. Package 1 is **not fully closed** until MFA ceremony, complete
mutation diff coverage, browser evidence, and production infrastructure gates
are completed and recorded.

## Recheck on 2026-09-26

- Focused Package 1 regression: **18 passed**.
- Database hardening check: **87 RLS-enabled tables** reported.
- Audit retention: **implemented in the audit helper with a seven-year
  retention timestamp**; production retention enforcement and monitoring remain
  infrastructure-dependent.
- Gitleaks: **9 findings in generated `website-next/.next` artifacts**; these
  are not yet cleared as verified false positives and must be removed from
  release artifacts or reviewed before release.
- `pip-audit`: unavailable in the current local PATH; the GitHub workflow
  installs it during hosted execution.
