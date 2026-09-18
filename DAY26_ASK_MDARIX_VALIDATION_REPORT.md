# MDARIX R1 — Day 26 Ask MDARIX Validation Report

## Evidence baseline

| Gate | Result |
|---|---|
| Targeted Day 26 tests | PASS — 14 passed |
| Full backend regression | PASS — 266 passed, 0 failed, 0 errors |
| Dependency warnings | 2 non-blocking deprecation warnings |
| Frontend production build | PASS |
| Python compilation | PASS |
| `git diff --check` | PASS |

## Security zero-gate matrix

The current checkpoint implements deterministic interpretation and typed
retrieval-scope contracts. It does not yet expose an authenticated Ask API,
persisted investigation sessions, executable authorized retrieval, or model
context construction. Therefore architectural intent is not counted as runtime
security evidence.

| Gate | Result | Evidence |
|---|---|---|
| Cross-tenant Ask leakage | NOT TESTED | No executable Ask endpoint |
| Cross-tenant AI context leakage | NOT TESTED | No model-context execution path |
| Cross-tenant InvestigationSession leakage | N/A | Session is a typed contract only |
| Hidden-field AI leakage | PARTIAL PASS | AI-safe scope contract; no model context runtime |
| Secret AI leakage | PARTIAL PASS | Existing Day 25 allowlist plus scope contract; no runtime context |
| Password/token leakage | PARTIAL PASS | Existing boundary tests; no Ask response endpoint |
| Authorization bypass | NOT TESTED | No Day 26 Ask authorization orchestration |
| Entitlement bypass | NOT TESTED | No Day 26 Ask entitlement endpoint |
| Role spoofing | PASS (interpreter scope) | Question text cannot alter retrieval scope |
| Tenant spoofing | PASS (interpreter scope) | Question text cannot alter tenant-scoped scope |
| ProductVersion spoofing | PARTIAL PASS | Version references are preserved; no authorized resolver |
| Arbitrary SQL execution | PASS (interpreter) | Interpreter produces typed specification only; no SQL execution |
| Prompt-based permission escalation | PASS (interpreter) | Authority text does not change scope flags |
| Unauthorized evidence retrieval | NOT TESTED | No executable retrieval path |
| Client-controlled authorization | NOT TESTED | No Ask API request model |
| Client-controlled tenant | NOT TESTED | No Ask API request model |
| Client-controlled entitlement | NOT TESTED | No Ask API request model |
| Approval through Ask | PASS (scope) | No approval/signature operations exist in interpreter |
| Electronic signature through Ask | PASS (scope) | No approval/signature operations exist in interpreter |
| Raw stack trace exposure | NOT TESTED | No Ask endpoint error surface |
| False success after dependency failure | NOT TESTED | No Ask execution dependency path |

## Semantic gates

### Product versus ProductVersion

PASS at interpretation level. Product-wide questions retain an empty version
scope; versioned questions retain the explicit revision; comparisons require two
versions and do not silently select a current version. Authorized product and
version resolution remains unimplemented and therefore is not claimed PASS.

### Temporal semantics

PASS at interpretation level. `What had happened by 2026-03-31?` produces
`EVENT_AS_OF`, while `What did we know as of 2026-03-31?` produces
`KNOWN_AS_OF`. `CURRENT` remains the default only when no historical temporal
anchor is stated.

### Controlled retrieval

PARTIAL. The chain through typed intent, temporal scope, ProductVersion
references, and AI-safe retrieval-scope metadata exists. Authentication,
tenant resolution, entitlement, permission checks, authorized retrieval, and
Reality Graph execution are not yet wired into an Ask operation.

### AI data boundary

PARTIAL. The interpreter always emits tenant-scoped, authorized-only,
AI-safe-field-only retrieval metadata and Day 25 provides the field allowlist.
No Day 26 model context is constructed, so runtime pre-context leakage cannot
yet be demonstrated.

### Session and follow-up reauthorization

N/A for executable behavior. `InvestigationSession` and `InvestigationQuery`
are typed contracts only; no persistence, continuation, ownership check, or
per-request reauthorization path is implemented.

## Day 27 readiness

PARTIAL, not PASS. The typed specification and retrieval-scope contract provide
an extension point for Reality Graph, Evidence, Change, Component, Supplier,
Lot, Timeline, Hypothesis, Challenger, Unknowns, Failure Chain, Counterfactual,
and Assurance capabilities. Runtime server-side authorization and controlled
retrieval must be implemented before Day 27 intelligence is safely enabled.

## Completion decision

Day 26 is **BLOCKED** for formal closure. No critical code defect was found in
the implemented interpreter foundation, but mandatory runtime security gates
remain untested because the controlled Ask API/execution plane is not yet
implemented. The completion commit is withheld.

