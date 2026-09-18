# MDARIX R1 — Day 27 Final Validation Report

## Status

**DAY 27: BLOCKED — LIVE TENANT A/B MATRIX PENDING**

Day 27 authorized retrieval foundation is implemented and the automated
database-backed synthetic isolation matrix passes. The authenticated live
Tenant A/B runtime matrix now also passes. Formal completion remains withheld
until the remaining runtime audit and dependency-failure evidence is executed.
Day 28 has not started.

## Entry gate

- Day 26 completion: PASS / formally closed.
- Starting repository HEAD: `043137b788400b8948f4a5ee017128a52f7c2641`.
- `HEAD == origin/main` at entry: YES.
- Day 26 implementation and UI changes were preserved.

## Implemented architecture

`POST /api/v1/ask/` now accepts optional Product, ProductVersion, and Evidence
scope identifiers. The server constructs an `AuthorizedRetrievalRequest` from
the authenticated tenant context. `AuthorizedRetrievalService` applies tenant
predicates, ProductVersion-to-Product relationship validation, explicit bounds
(maximum 100), safe field serialization, and the existing AI pre-model
allowlist. Client tenant, role, entitlement, question text, and identifiers
are never authorization authority.

Retrieval failures return a controlled `503 RETRIEVAL_UNAVAILABLE` response
with correlation continuity and a safe audit event. Retrieval is read-only.

## Automated database-backed synthetic matrix

The automated fixture uses the repository's configured `SessionLocal` and
inserts fresh random synthetic Tenant A/B canaries into the test database.
The fixture exercises the actual SQLAlchemy retrieval queries, then removes
only the exact rows it created during teardown. No real operator or customer
identifiers are used, and the fixture does not run as a production endpoint.
The live fixture script now resolves the repository root when invoked directly
from `scripts/`, and the live matrix reuses the repository's declared `httpx`
client rather than requiring an undeclared `requests` dependency.

| Gate | Result |
|---|---|
| Tenant A positive Product/Version/Evidence | PASS |
| Tenant B positive Product/Version/Evidence | PASS |
| Cross-tenant Product exclusion | PASS |
| Cross-tenant ProductVersion exclusion | PASS |
| Cross-tenant Evidence exclusion | PASS |
| Same-tenant Product/ProductVersion mismatch | PASS |
| Tenant-scoped AI-safe context | PASS |
| Synthetic canary leakage | 0 |
| Bounded retrieval | PASS |
| Client authority spoofing | PASS via preserved Day 26 tests |
| Session ownership/isolation | PASS via preserved Day 26 tests |
| Non-mutation | PASS via preserved Day 26 tests |

Fixture result: **3 passed, 0 failed, 0 errors** for the real database-backed
retrieval fixture. Combined focused result: **9 passed, 0 failed, 0 errors**
for the Day 27 retrieval fixture and Day 26 API subset. Full backend regression: **287 passed, 0 failed, 0 errors,
3 warnings**. Warnings are dependency/cache deprecations.

## Safety and provenance

Product, ProductVersion, and Evidence responses use explicit safe fields and
retain available source/provenance metadata. Evidence remains source evidence;
no fact, hypothesis, causality, root cause, or human decision is inferred.

No arbitrary SQL, approval/signature execution, unauthorized mutation, secret
leakage, raw-stack leakage, or hidden chain-of-thought leakage was observed.

## Live authenticated Tenant A/B matrix

Using synthetic development identities and data only, the live API matrix
completed successfully after fixture password rotation.

| Case group | Result |
|---|---|
| Tenant A Product, ProductVersion, Evidence | 3 PASS; one authorized record each |
| Tenant B Product, ProductVersion, Evidence | 3 PASS; one authorized record each |
| Tenant A requesting Tenant B identifiers | 3 PASS; zero authorized records |
| Tenant B requesting Tenant A identifiers | 3 PASS; zero authorized records |
| Total live matrix | **12 PASS, 0 FAIL** |

The matrix used authenticated sessions and the existing `POST /api/v1/ask/`
route. The API health check reported the database as reachable.

The explicit session-ownership case also passed: Tenant A created an active
investigation session, Tenant B attempted to reuse its session identifier, and
the API returned `404 ASK_SESSION_NOT_FOUND` without returning Tenant A data.

Persisted audit proof passed in the live `mdarix_r1` database. The matrix
correlation IDs retained `ASK_QUERY_RECEIVED`, `ASK_RETRIEVAL_EXECUTED`, and
`ASK_QUERY_PROCESSED` rows for successful scoped retrievals, with
`result_count=1` for same-tenant canaries and `result_count=0` for foreign
identifiers. The session-reuse correlation retained `ASK_QUERY_RECEIVED` and
`ASK_AUTHORIZATION_DENIED` with reason `ASK_SESSION_NOT_FOUND`. Actor and
tenant IDs were consistent with the authenticated synthetic A/B sessions.

## Live dependency-failure proof

The controlled development-only fault flag was enabled on a separate backend
port and exercised through an authenticated Tenant A scoped retrieval. The
required correlation ID was `DAY27-LIVE-DEPENDENCY-FAILURE-001`.

| Gate | Result |
|---|---|
| HTTP response | **503 PASS** |
| Error code | **RETRIEVAL_UNAVAILABLE PASS** |
| Persisted audit row | **ASK_RETRIEVAL_FAILED PASS** |
| Audit details | Safe `RETRIEVAL_UNAVAILABLE` reason only |
| Correlation, actor, tenant attribution | PASS |
| Fabricated retrieval data | 0 |
| Secrets/raw traceback/filesystem/database details | 0 |
| Recovery retrieval after fault disable | **PASS**; normal Tenant A/B matrix recovered |

## Remaining hard gates

The following are not yet claimed as PASS:

1. No additional dependency-failure gate remains; recovery passed.

## Live client-spoofing runtime proof

The authenticated synthetic Tenant A/B runtime matrix exercised all six
required spoofing cases. Client-supplied tenant, role, entitlement, session,
identifier, and prompt claims did not replace server-derived authority.

| Case | Result |
|---|---|
| Tenant spoofing | PASS |
| Role spoofing | PASS |
| Entitlement spoofing | PASS |
| Combined authority spoofing | PASS |
| Prompt-based escalation | PASS |
| Foreign session reuse with spoofed claims | PASS; controlled 404 denial |
| Authorization escalation count | **0** |
| Cross-tenant records returned | **0** |
| Canary leakage | **0** |
| Secret/raw-stack leakage | **0** |

The matrix used authenticated sessions and sanitized output only. No
credentials, cookies, tokens, session identifiers, or protected record content
were written to the report. Existing persisted audit evidence retains the
server-derived actor and tenant attribution for these correlations.

Persisted spoof audit inspection passed: User A spoof correlations retained the
server-derived Tenant A attribution and safe `result_count=0` retrieval records.
The foreign-session correlation retained the authenticated Tenant B attribution
and recorded `ASK_AUTHORIZATION_DENIED` with `ASK_SESSION_NOT_FOUND`. No
client-supplied Tenant B claim became authoritative.

The authorized retrieval path is read-only for Product, ProductVersion, and
Evidence. The remaining completion action is final nonmutation/database-delta
confirmation before the Day 27 completion commit.

## Live nonmutation / database-delta proof

The live database schema inventory confirmed the protected domain and governance
tables present in the R1 schema. Exact synthetic canary snapshots showed that
Tenant A/B Product, ProductVersion, Evidence, Investigation, and Tenant rows
were last updated during fixture provisioning at 08:05 UTC, before the live
Ask retrieval, spoofing, dependency-failure, and recovery runs. No protected
domain row was updated by Ask execution.

Synthetic AuthUser timestamps at 08:11 UTC reflect the documented fixture
password rotation performed before live authentication; this is fixture
provisioning/operational setup, not retrieval mutation. Ask execution created
only expected audit and session operational records.

| Assertion | Result |
|---|---|
| Protected Product mutations | **0** |
| Protected ProductVersion mutations | **0** |
| Protected Evidence mutations | **0** |
| Protected Investigation mutations | **0** |
| Tenant authority mutations | **0** |
| Persisted role escalation | **0** |
| Persisted entitlement escalation | **0** |
| Session ownership corruption | **0** |
| Approval/signature mutations | **0** |
| Unauthorized regulated writes | **0** |
| Expected operational deltas | Audit events, Ask sessions, synthetic fixture password rotation |

**LIVE NONMUTATION: PASS**

**UNAUTHORIZED REGULATED WRITES: 0**

## Validation

- Frontend production build: PASS.
- Python compilation: PASS.
- `git diff --check`: PASS.
- Migration: NONE; Day 27 uses existing tables and does not require schema
  changes.
- Critical defects: 0 observed.
- High defects: 0 observed.

## Day 28 handoff

Day 28 remains **NOT STARTED**. Its planned scope is Cross-System Lifecycle
Retrieval: Complaint → Product → ProductVersion → Change → Component →
Supplier → Site → Lot/Batch → Requirement → Risk → FailureMode → Control →
Evidence.

No Day 27 completion commit or push is authorized while the live runtime gate
remains pending.
