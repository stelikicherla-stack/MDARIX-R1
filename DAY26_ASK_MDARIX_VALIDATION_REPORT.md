# MDARIX R1 — Day 26 Ask MDARIX Final Validation Report

## Validation result

Day 26 is **PASS / FORMALLY CLOSED** for the implemented controlled-foundation
scope. The completion commit is `667404b` (`feat: complete MDARIX R1 Day 26
Ask MDARIX foundation`) and has been pushed to `origin/main`.

## Authentication authority remediation

The runtime blocker was traced to `auth_service = LocalAuthService()` keeping
accounts in process memory while signup separately persisted `auth_users` in
PostgreSQL. After restart, signin searched the empty in-memory account map.

Signin now queries the persisted `auth_users` row, verifies the existing scrypt
hash, validates ACTIVE/verified state, and creates the existing HttpOnly
ephemeral `mdarix_session`. Session context remains server-derived. No schema
change or migration was required; the live head remains `j26asksessions`.

Focused remediation tests: **15 passed, 0 failed, 0 errors**.
Final full regression after remediation: **283 passed, 0 failed, 0 errors,
3 warnings**. Frontend build, Python compilation, and diff check passed.
The three warnings remain dependency/cache warnings and are non-blocking.

## Live runtime closure evidence

The live R1 operator verification completed after the `ASK_MDARIX` entitlement
was provisioned through the existing governance bootstrap path.

Successful authenticated Ask:

- Correlation ID: `DAY26-MANUAL-SUCCESS-002`
- Result: `INTERPRETED`
- Session: persisted (identifier redacted from repository documentation)
- Server actor: authenticated actor (identifier redacted from repository documentation)
- Server tenant: authenticated tenant (identifier redacted from repository documentation)
- Server role: `Viewer`
- Execution: `CONTROLLED_FOUNDATION_ONLY`
- Persisted events: `ASK_QUERY_RECEIVED`, `ASK_QUERY_PROCESSED`

Denied authenticated Ask:

- Correlation ID: `DAY26-MANUAL-DENIED-002`
- Result: controlled `ASK_SESSION_NOT_FOUND`
- Persisted events: `ASK_QUERY_RECEIVED`, `ASK_AUTHORIZATION_DENIED`
- Denial reason: `ASK_SESSION_NOT_FOUND`

Both audit queries confirmed matching server actor, tenant, correlation ID,
safe details, and timestamps. Persisted audit/correlation closure: **PASS**.

The required Tenant A/B Product/ProductVersion/Evidence matrix is explicitly
deferred to Day 27 because the Day 26 endpoint does not execute those
retrievals.
The current Day 26 `POST /api/v1/ask/` contract accepts question and optional
session context, but does not execute Product, ProductVersion, or Evidence
record retrieval or expose those resource IDs as authorization inputs. The
matrix therefore cannot be honestly marked PASS without adding retrieval
functionality outside the Day 26 foundation scope.

## Final scope reconciliation

Day 26 is closed against its implemented controlled-foundation surface. It
provides authenticated Ask, server-derived identity/tenant/role, persisted
server-side entitlement, owned investigation sessions, interpretation,
Investigation Specification, bounded retrieval planning, the AI/privacy
boundary, audit/correlation, and a controlled foundation response.

The following are explicitly **DEFERRED TO DAY 27 — NOT YET EXECUTABLE** and
are not represented as tested Day 26 passes:

- Product runtime isolation
- ProductVersion runtime isolation
- Evidence runtime isolation
- Retrieved AI/model-context isolation
- Cross-system lifecycle investigation retrieval

When Day 27 introduces those execution surfaces, its mandatory entry tests are
Tenant A/B symmetric Product, ProductVersion, and Evidence allow/deny cases;
mismatched Product/ProductVersion denial; cross-tenant and same-tenant session
denial; client tenant/role/entitlement spoofing resistance; retrieval-plan and
result zero leakage; and AI-safe context zero leakage using synthetic canaries.

## Implemented Day 26 closure gates

| Gate | Result |
|---|---|
| Authentication restart persistence | PASS |
| Server-derived tenant and role | PASS |
| Persisted `ASK_MDARIX` entitlement | PASS |
| Client tenant/role/entitlement spoofing resistance | PASS |
| Session ownership and cross-tenant session denial | PASS |
| Query-text authorization escalation resistance | PASS |
| Investigation Specification authority boundary | PASS |
| Tenant-scoped bounded retrieval plan | PASS |
| Arbitrary SQL capability | 0 |
| Ask mutation/approval/signature capability | 0 |
| Successful live Ask | PASS |
| Successful persisted audit | PASS |
| Controlled denied Ask | PASS |
| Denied persisted audit | PASS |
| Correlation continuity | PASS |
| Secret leakage | 0 |
| Raw stack leakage | 0 |
| Critical defects | 0 |
| High security defects | 0 |

Scope reconciliation result: **Day 26 blockers = 0**. Day 27 remains not
started. The formal completion commit was created after final validation and
Git verification.

## Ask entitlement provisioning remediation

Live inspection found the active `R1_GOVERNANCE_DEMO` plan had only
`DECISION_CENTER_SIGNATURES`; no persisted plan contained `ASK_MDARIX`.
The Ask authorization check was correctly fail-closed, so live Ask requests
were denied without generating successful audit events.

The existing governance `bootstrap()` mechanism is now idempotently extended
to provision an enabled, ACTIVE `ASK_MDARIX` feature on `R1_GOVERNANCE_DEMO`.
It does not special-case a user or tenant and does not change `_has_ask_entitlement()`.
No migration was required.

Focused entitlement/auth/Ask tests: **16 passed, 0 failed, 0 errors**.
Full regression after provisioning change: **284 passed, 0 failed, 0 errors,
3 warnings**. Frontend build, Python compilation, and diff check passed.

Legitimate live provisioning command, after authenticating against the R1
backend, is the existing governance bootstrap path:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri 'http://127.0.0.1:8007/api/v1/governance/effective-access' `
  -WebSession $AuthenticatedSession
```

This uses the authenticated tenant context and creates only missing
configuration rows. It must not be replaced with direct SQL inserts.

Read-only verification:

```powershell
docker exec mdarix-r1-postgres psql -U mdarix_app -d mdarix_r1 -c "SELECT p.code, p.status, f.feature_code, f.enabled, f.status AS feature_status FROM plan_definitions p JOIN feature_entitlements f ON f.plan_id = p.id WHERE p.code = 'R1_GOVERNANCE_DEMO' AND f.feature_code = 'ASK_MDARIX';"
```

Security-closure checkpoint: `9691da2` plus the executable closure tests,
Ask audit-boundary changes, and customer-safe error handling in the current
working state.

## Implementation baseline

The validated implementation includes checkpoints `d8aa5a5`, `d6db40a`,
`4170338`, `108b9d2`, `4e1cc27`, `2d4946f`, and `899f64e`:

- typed Ask investigation contracts and deterministic interpretation;
- authenticated Ask API with server-derived identity and tenant context;
- runtime tenant status and Ask entitlement enforcement;
- persisted investigation-session ownership and per-request reauthorization;
- bounded, tenant- and authorization-scoped retrieval planning;
- ProductVersion and temporal-scope preservation;
- pre-model AI-safe context boundary and controlled model boundary.

Live migration evidence previously verified: `j26asksessions (head)` and
`public.investigation_sessions`.

## Executed automated evidence

| Gate | Result | Evidence |
|---|---|---|
| Focused Day 26 suite | PASS | 29 passed, 0 failed, 0 errors |
| Expanded focused/security suite | PASS | 27 passed, 0 failed, 0 errors, 3 warnings |
| Final focused/security suite | PASS | 28 passed, 0 failed, 0 errors, 3 warnings |
| Final focused/security suite after error handling | PASS | 29 passed, 0 failed, 0 errors, 3 warnings |
| Final full backend regression | PASS | 284 passed, 0 failed, 0 errors, 3 warnings |
| Frontend production build | PASS | `npm.cmd --prefix frontend run build` |
| Python compilation | PASS | `compileall` for backend, Ask, and counterfactual packages |
| `git diff --check` | PASS | no whitespace errors |

Warnings are dependency/cache warnings: Starlette/httpx deprecation, anyio
deprecation, and a pytest cache-path warning. They are not test failures.

## Runtime security gate status

The focused tests prove anonymous denial, server-context use, client-authority
ignorance, bounded tenant-scoped retrieval planning, unresolved-query blocking,
and prompt/SQL text remaining data rather than authority. The following items
are outside the Day 26 executable surface and are mandatory Day 27 validation
items:

- controlled Tenant A/Tenant B fixtures for product, ProductVersion, session,
  evidence, retrieval, and pre-model context isolation;
- entitlement revocation and per-request permission/user/tenant reauthorization;
- session-owner, ProductVersion, and field-level authorization matrix;
- instrumented pre-model payload inspection for all secret classes;
- dependency failure injection across retrieval, database, model, timeout, and
  malformed-response paths;
- audit event and correlation continuity verification;
- complete prompt-injection authority-escalation matrix;
- explicit zero counts for every required security gate.

They are deferred rather than treated as Day 26 failures or unsupported
passes.

## Security zero-gate matrix

The following executable checks now provide zero findings for the tested
boundaries: pre-model hidden-field/secret sentinel exclusion, cross-tenant
context exclusion, prompt authority text not changing scope, hard retrieval
bounding, and Ask action non-mutation. Product/ProductVersion/Evidence runtime
retrieval remains deferred because those execution surfaces belong to Day 27.

| Gate | Result |
|---|---|
| Cross-tenant AI-context leakage | 0 in executable boundary tests |
| Hidden-field AI leakage | 0 in executable boundary tests |
| Secret AI leakage | 0 for supplied sentinel fields |
| Prompt permission escalation | 0 in interpreter/boundary tests |
| Arbitrary SQL execution | 0 in interpreter/boundary tests |
| Approval/signature/closure through Ask | 0 in current boundary tests |
| Cross-tenant Ask/session leakage | 0 in implemented session boundary tests and live denied path |
| Authorization/entitlement bypass | 0 in implemented Ask boundary tests and live entitlement path |
| Role/tenant/session-owner spoofing | 0 in implemented authority/session tests |
| Unauthorized evidence retrieval | DEFERRED TO DAY 27 — NOT YET EXECUTABLE |
| Dependency false success | N/A — no Day 27 retrieval/provider boundary exists |
| Audit secret leakage/correlation continuity | PASS — persisted live success and denial rows verified |
| Raw stack traces | PASS for unexpected Ask exception path | API test confirms sanitized HTTP 500, correlation retained, no traceback or sentinel |

The current Day 26 endpoint does not invoke a retrieval repository or AI
provider. Retrieval-failure injection, provider-unavailable, timeout, and
malformed-provider-response tests are therefore **N/A for this foundation**;
there is no executable provider/repository boundary to inject without adding
Day 27 functionality. This is a technical scope limitation, not a PASS.

An unexpected Ask dependency exception is now normalized by the application
error handler and tested through the API: HTTP 500, safe `INTERNAL_ERROR`,
correlation ID retained, no traceback or secret sentinel.

The remaining Tenant A/B and persisted-audit items cannot be honestly promoted
to PASS from the current harness: the Day 26 Ask endpoint does not resolve
Product, ProductVersion, or Evidence records, and the tests do not connect to
the live database to inspect committed Ask audit rows. They remain explicit
blockers rather than being inferred from unit-level boundary tests.

Critical defects: 0 observed. High security defects: 0 observed. Unproven is
not treated as zero for the formal completion gate.

## Semantic and boundary assessment

- Product and ProductVersion semantics: PASS in the validated specification and
  retrieval-plan boundary; full authorized resolver matrix remains pending.
- Temporal semantics: PASS for CURRENT, EVENT-AS-OF, and KNOWN-AS-OF handling;
  follow-up runtime preservation remains pending explicit evidence.
- Controlled retrieval: PASS for bounded plan construction and tenant/
  authorization metadata; complete repository result isolation remains pending.
- AI-safe context: PASS at the implemented boundary contract; pre-model payload
  inspection remains pending for the full secret matrix.
- Ask cannot approve, sign, close, or mutate governed records in the current
  boundary.
- Unsupported causal conclusions are not generated by the Day 26 foundation.

## Day 27 readiness

**READY / NOT STARTED.** Day 26 is formally closed for its implemented scope;
Day 27 begins with authorized Product/ProductVersion/Evidence retrieval and
the mandatory Tenant A/B isolation matrix.

## Completion decision

Day 26 is **PASS / COMPLETE / FROZEN** for the controlled natural-language
investigation foundation. Product/ProductVersion/Evidence runtime isolation
and retrieved AI-context isolation remain mandatory Day 27 hard gates and are
not waived. Day 27 was not started by this closure.
