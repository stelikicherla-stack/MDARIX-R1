# MDARIX compliance validation protocol

This document records what the application enforces and what still requires a
controlled operational environment. It is evidence guidance, not a regulatory
certification.

## Application controls

- Authentication is durable, tenant-bound, throttled, and lockout-protected.
- Passwords are scrypt-hashed; password reuse is rejected against the current
  password and the last five recorded hashes. Password expiry defaults to 90
  days and is configurable through `MDARIX_PASSWORD_MAX_AGE_DAYS`.
- Audit events support actor, tenant, timestamp, correlation, source IP,
  user-agent, reason, old values, new values, and a seven-year retention date.
  Secret-like values are redacted before persistence.
- Audit rows are append-only through the database immutability trigger.
- Governed signatures require re-authentication, current object version,
  approval authority, segregation-of-duties checks, remarks, and a durable
  signature hash. Set `MDARIX_REQUIRE_MFA_FOR_SIGNATURES=true` to fail closed
  until the configured identity provider has supplied MFA enrollment and
  verification evidence.
- `GET /api/v1/governance/decisions/{decision_id}/signature-verification`
  recomputes the content fingerprint and signature hash and reports validity.

## Required test evidence

1. Sign in with a valid and invalid password; capture lockout and audit IDs.
2. Prove password reuse is rejected and expiry blocks sign-in.
3. Execute a governed approval with a reason and verify the stored actor,
   source IP, user-agent, reason, timestamp, and signature hash.
4. Tamper-test a signature row in an isolated database and prove verification
   reports invalid; prove direct UPDATE/DELETE is rejected by the trigger.
5. Run the audit export as two tenants and verify there is no foreign data.
6. Run the retention report and verify every audit row has a retention date.

## Operational gates still required

Digital certificate issuance/rotation, MFA delivery or an external IdP
ceremony, seven-year retention enforcement in backup/archive storage, TLS
certificates, PITR/WAL archiving, restore rehearsal, production monitoring and
alert routing, and browser accessibility evidence require approved deployment
infrastructure. They must remain **PENDING — production infrastructure
required** until those controls are exercised and recorded.
