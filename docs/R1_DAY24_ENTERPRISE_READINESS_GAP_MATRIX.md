# MDARIX R1 Day 24 — Enterprise Readiness Gap Matrix

## Scope and status convention

This is the initial Day 24 pre-development inventory. `IMPLEMENTED` means code or documentation was found; it is not a passing validation result. A capability becomes `PASS` only after targeted evidence is executed. Day 23 manual acceptance is currently recorded as provisional and requires later re-execution.

| Capability | Current State | Evidence | Gap | Risk | Required Action | Test Required | Final Status |
|---|---|---|---|---|---|---|---|
| Day 23 dependency | Implemented; provisional manual status | Day 23 report, governance tests | Five journeys require repeat confirmation | High | Re-run journeys before final Day 24 freeze | Day 23 manual suite | PENDING |
| Privacy / PII / PHI | Partially implemented | Day 21 field-permission tests and policy docs | No unified privacy metadata/control path demonstrated | High | Define classification and enforce API/UI/AI/export boundaries | PRIVACY-001+ | NOT TESTED |
| AI data boundary | Partially implemented | Investigation workspace and retrieval services | No explicit provider-neutral boundary record or complete leakage matrix | High | Add controlled context policy and provenance checks | AI-BOUNDARY-001+ | NOT TESTED |
| Retention / disposition | Documentation only | Existing schema/docs search | No tenant policy, hold, eligibility, or audited disposition workflow found | High | Design safe disposition foundation | RETENTION-001+ | MISSING |
| OIDC / SSO readiness | Partially implemented | Local auth and session APIs | Provider abstraction and tenant policy are not demonstrated | Medium | Document local-only R1 and add provider configuration foundation if needed | SESSION-001+ | NOT TESTED |
| Session security | Partially implemented | Auth service and Day 23 re-auth tests | Expiry/revocation/suspension matrix incomplete | High | Add targeted session lifecycle tests | SESSION-010+ | NOT TESTED |
| Secret management | Documentation / partial controls | Password hashing and frontend source review | No complete secret inventory and automated scan report | High | Create secret-management policy and scan gates | SECRET-001+ | NOT TESTED |
| Connector failure model | Partially implemented | Integration gateway tests | Operational states and safe failure diagnostics need evidence | High | Validate retry, failure, idempotency, and reconciliation states | CONNECTOR-001+ | NOT TESTED |
| Reconciliation | Partially implemented | Day 20 integration tests | Full accounting invariants and tenant scoping need evidence | High | Add invariant-focused tests and report | RECON-001+ | NOT TESTED |
| Connector health | Missing / not exposed | No administration health surface found | No connector health summary endpoint/UI | Medium | Define safe health contract or document limitation | HEALTH-010+ | MISSING |
| Operational health | Partially implemented | `/health` in `backend/app/main.py` | Only basic database reachability is exposed | Medium | Add safe dependency/readiness checks | HEALTH-001+ | NOT TESTED |
| Support diagnostics | Missing | No support package capability found | No safe metadata-only diagnostic export | Medium | Design redacted diagnostic package | SUPPORT-001+ | MISSING |
| Controlled export | Missing / not demonstrated | No dedicated export router found | Privacy, field, tenant, temporal, and audit gates unproven | High | Implement controlled export foundation | EXPORT-001+ | MISSING |
| Backup / restore | Documentation only | PostgreSQL environment documented | Separate-target restore evidence absent | High | Execute safe backup and restore validation | BACKUP-001+ | BLOCKED |
| Configuration lifecycle | Partially implemented | Existing migration/configuration files | Versioned change approval and audit evidence incomplete | Medium | Inventory configuration surfaces and controls | CONFIG-001+ | NOT TESTED |
| Compliance language | Partially implemented | Existing validation and limitation docs | Full repository scan not yet executed | Medium | Scan and correct unsupported claims | SECURITY-020 | NOT TESTED |
| Performance envelope | Documentation only | No Day 24 execution evidence | Operating limits and bounded AI context unproven | Medium | Define representative workload and limits | PERF-001+ | NOT TESTED |
| Known limitations | Implemented | `docs/R1_KNOWN_LIMITATIONS.md` | Must be updated with Day 24 findings | Low | Maintain evidence-linked limitations | Review | IN PROGRESS |

## Initial release recommendation

Do not create the Day 24 completion commit from this inventory. The first required work product is the targeted gap closure plan and evidence set, with backup/restore, export, privacy/AI boundary, and connector reliability treated as release-blocking until demonstrated.
