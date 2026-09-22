# MDARIX R1 Future Architecture — Stage 1 Security Findings

Status: **P0 findings identified; Stage 2 remediation required before MVP GO**

## P0 findings

| ID | Finding | Evidence | Impact | Required correction |
|---|---|---|---|---|
| SEC-P0-01 | Tenant-owned legacy routes permit anonymous fallback to `ACME_CARE_SYNTHETIC`/first tenant. | `backend/app/evidence/router.py:16-32`; `backend/app/investigations/router.py:38-48`; `backend/app/decision_router.py:20-59`; `backend/app/retrieval/router.py:16-25`; `counterfactual/router.py` | Unauthenticated callers may access or mutate the default tenant through Product, Evidence, Investigation, Retrieval, Decision, Trust, Evaluation, or Counterfactual paths. | Add one required `AuthenticatedRequestContext`; remove all anonymous tenant fallback; return 401 before service execution. |
| SEC-P0-02 | Graph and Product360/timeline endpoints do not consistently require authenticated context. | `backend/app/main.py:94-190`; `graph/service.py:10`; `backend/app/product360/service.py:10` | Customer-owned lifecycle and graph data can be exposed outside the authenticated tenant boundary. | Require shared context and pass server-derived tenant through every service call. |
| SEC-P0-03 | Client-controlled or weakly derived tenant context exists in legacy paths. | `backend/app/integration_router.py`; `backend/app/auth_router.py:20-23`; default-tenant helpers | A browser-supplied or arbitrary first-tenant association can mis-scoped data and new accounts. | Derive tenant only from authenticated membership or authorized platform-admin target selection; validate composite tenant/entity ownership. |
| SEC-P0-04 | Authentication state is process memory. | `auth/service.py:14-15,24-51,63-72` | Restart, multi-worker deployment, or horizontal scaling invalidates sessions/tokens unpredictably; revocation is not durable. | Add durable AuthSession, invitation, reset, and authentication-event records; hash tokens; revoke on password/status changes. |
| SEC-P0-05 | Production cookie configuration is unsafe by default. | `backend/app/auth_router.py:41-42` sets `secure=False` | Session cookies may travel over insecure transport if deployed incorrectly. | Make Secure mandatory outside explicit local development; configure SameSite/domain/expiry centrally and add startup refusal for unsafe production configuration. |
| SEC-P0-06 | Development activation/reset tokens can be returned to the browser when email is not configured. | `backend/app/auth_router.py:58-60,94-98`; admin invitation response | A fallback intended for local development can leak account activation capability in a non-development environment. | Permit development tokens only under an explicit local profile; production returns a generic delivery result and logs only a redacted correlation. |
| SEC-P0-07 | Invitation email delivery and database state are not transactionally coordinated. | `backend/app/access_router.py:477-485`; `auth/emailer.py:30-61` | Email may be delivered before a later database commit, or durable state may fail after a token is issued. | Use an outbox with durable hashed token and delivery state; commit domain change and outbox atomically; deliver asynchronously with retry/idempotency. |

## P1 findings

- `backend/app/enterprise_audit.py:6-9` performs shallow key filtering; nested secret values can survive. Replace with recursive redaction and structured allowlists.
- The audit schema does not guarantee actor display snapshot, changed fields, old/new values, source/channel, previous/resulting version, reason, or approval context for every governed transition.
- `backend/app/access_router.py:633-667` uses a generic dynamic `setattr` patch endpoint. Replace with resource-specific command schemas and validation.
- UI decision requests contain hardcoded reviewer identifiers (`frontend/src/main.tsx:661-665`) instead of authenticated actor context.
- Rate limiting, lockout enforcement, MFA/SSO, session revocation, and security-event monitoring are not complete.
- Platform/customer admin scope is inconsistently exposed: platform-admin cross-tenant creation exists, while listing/management is tenant-filtered in `access_router.py:435-439`.

## Security disposition

The secure newer routes and audit trigger are useful foundations, but the legacy route set creates a split security model. MVP is **NO-GO** until there is one request-context dependency and every tenant-owned route rejects unauthenticated access before resolving data.
