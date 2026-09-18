# MDARIX R1 - Day 30 Final Validation Report

## Scope

Day 30 covers persisted Evidence, Hypothesis, Unknown, provenance, tenant
isolation, controlled dependency failure/recovery, and read-only behavior.
Day 31 has not started.

## Validation gates

| Gate | Status |
|---|---|
| Live Tenant A evidence/hypothesis/unknown/provenance | PASS |
| Live Tenant B evidence/hypothesis/unknown/provenance | PASS |
| Cross-tenant isolation and canary leakage | PASS; leakage 0 |
| Persisted DAY30 audit proof | PASS |
| Controlled dependency failure | PASS; 503 RETRIEVAL_UNAVAILABLE |
| Controlled recovery | PASS; Tenant A and B restored |
| Read-only nonmutation | PASS; zero count and fingerprint changes |
| Focused compatibility tests | PASS; 25 passed, 2 warnings |
| Day 27 authorization test | PASS; 3 passed |
| Complete backend regression | PASS; 293 passed, 0 failed, 0 errors |
| Frontend build and compilation | PASS |
| Python compilation | PASS |
| Security zero-gate review | PASS; no suspicious audit secrets |

## Implementation checkpoint

- Hypothesis generation materializes validated Hypothesis, Unknown, and
  HypothesisEvidence projections idempotently and tenant-scoped.
- Ask retrieval exposes tenant-scoped intelligence for an authorized
  investigation, including hypotheses, unknowns, and provenance links.
- The controlled dependency fault seam supports DAY30_LIVE_DEPENDENCY_FAILURE.

## Live validation evidence

Tenant A and Tenant B authorized retrieval each returned one evidence-backed
intelligence result with one hypothesis, one unknown, and one provenance link.
Foreign-tenant retrieval returned zero records and zero canary leakage for
evidence, hypotheses, unknowns, and provenance.

Persisted audit evidence included DAY30-LIVE-DEPENDENCY-FAILURE with
ASK_QUERY_RECEIVED and ASK_RETRIEVAL_FAILED (RETRIEVAL_UNAVAILABLE), plus
successful DAY30-LIVE-RECOVERY-002 and DAY30-LIVE-B-RECOVERY audit chains
with retrieval result count 1.

## Final nonmutation evidence

Protected tables tested:

`products`, `product_versions`, `components`, `suppliers`,
`manufacturing_sites`, `lot_batches`, `requirements`, `changes`, `complaints`,
`investigations`, `risks`, `failure_modes`, `controls`, `evidence`,
`hypotheses`, `unknowns`, `decisions`, `product_components`,
`product_suppliers`, `component_suppliers`, `lot_components`,
`investigation_complaints`, `investigation_evidence`, `hypothesis_evidence`,
`reality_relationships`.

The BEFORE and AFTER snapshots used row counts and deterministic MD5
fingerprints generated from complete row content. Compare-Object returned no
differences for any of the 26 protected tables.

| Result | Value |
|---|---:|
| Protected tables tested | 26 |
| Protected domain row-count delta | 0 |
| Protected domain content changes | 0 |
| Unauthorized regulated writes | 0 |
| Read-only nonmutation | PASS |

The read-only window covered authorized Tenant A and B evidence, hypothesis,
unknown, provenance, investigation-context, current, temporal, and
cross-tenant zero-result retrievals. Audit, authentication, session, and
telemetry tables were excluded because request processing may write operational
records there.

## Historical checkpoint

Day 29 entry gate was PASS/FROZEN at `ec925e9`. Earlier Codex execution-
environment access limitations are historical evidence only; live validation
was executed through host Windows PowerShell against the R1 PostgreSQL database.

## Final authoritative status

**DAY 30 FINAL STATUS: COMPLETE**

READ-ONLY NONMUTATION = PASS
PROTECTED DOMAIN MUTATIONS = 0
UNAUTHORIZED REGULATED WRITES = 0

Day 31 remains **NOT STARTED**.
