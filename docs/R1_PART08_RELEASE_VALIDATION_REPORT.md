# MDARIX MVP 1.0 — Part 08 Integration, Security Verification & Design-Partner Release

Status: **NO-GO for design-partner release pending external and browser evidence**

Validation date: 2026-09-24
Scope: Parts 1–7 integration and release-gate verification. This report records only evidence observed in the current workspace and local runtime.

## 1. Evidence summary

| Gate | Result | Evidence |
|---|---|---|
| Python runtime | PASS | `.venv` Python 3.13.15 |
| Full backend regression | PASS | 381 passed, 3 non-blocking serializer/deprecation warnings |
| Frontend production build | PASS | TypeScript and Vite build passed; 1,875 modules transformed |
| Python compilation | PASS | `backend`, `briefs`, `scenario_intelligence`, `source_simulator`, `integration`, `reports` |
| Migration chain | PASS locally | Alembic current: `y41subscriptionlifecycle` (head) |
| PostgreSQL/pgvector | PASS locally | `pgvector/pgvector:pg16`, container healthy, host port 5433 |
| Backend health | PASS locally | `/health` returned `status=ok`, `database=reachable` |
| Simulator isolation stack | PASS locally | TrackWise 8101, PLM 8102, ERP 8103, Supplier 8104 each healthy with isolated DB |
| Compose configuration | PASS | `docker compose config --quiet` |
| Public UI render | LIMITED PASS | Local homepage, responsive render, MedTech visual, footer and Pricing evidence captured |
| Full browser route/link review | NOT PROVEN | Requires browser execution across every route and link |
| Three-tenant lifecycle | NOT PROVEN | Requires live authenticated browser/API evidence with three seeded tenants and plans |
| Production SMTP/Resend | NOT PROVEN | Local credentials/provider delivery not part of this run |
| Live GenAI provider | NOT PROVEN | No live provider credential or response evidence |
| Production object storage | NOT PROVEN | Local object-storage abstraction only |
| Multi-instance sessions | NOT PROVEN | No deployed multi-instance environment exercised |
| Hosted CI | NOT PROVEN | Local checks passed; GitHub-hosted run not observed |

## 2. Parts 1–7 integration inventory

Implemented or locally evidenced:

- Shared authenticated request context, tenant-aware authorization, session and entitlement primitives.
- Platform and customer administration routes and frontend control-plane surfaces.
- Mapping catalog, versioning, tenant override, validation, dry-run and schema-drift tooling.
- Product, investigation, evidence, retrieval, Ask MDARIX, decision, trust, evaluation and counterfactual surfaces.
- Supplier-evidence, communication, report catalog, subscription lifecycle, outbox and simulator integration foundations.
- Public MDARIX website routes, consistent design system, Pricing route, full footer navigation, MedTech imagery and lifecycle visuals.
- Durable migration chain through the current Alembic head.

Limited or requiring operational proof:

- Provider integrations use deterministic local simulator contracts; real customer endpoints and credentials are not configured.
- Email and GenAI paths have configured-code/test coverage, but live provider delivery/execution is not proven in this report.
- Browser evidence currently covers local public-site renders; complete persona, tenant, keyboard, screen-reader and end-to-end evidence remains open.

## 3. Required Part 08 security and lifecycle gates

The following must be run with redacted evidence before a release GO:

1. Three separate customer tenants with different plans, seats, personas, fields and release availability.
2. Platform Admin provisioning through invitation acceptance, Customer Admin setup, user creation and seat enforcement.
3. Connector import with provenance, investigator review, AI uncertainty, separate approver signature, mapping adoption and license lifecycle.
4. Cross-tenant attacks against route IDs, search, exports, attachments, cache keys, workers and AI prompts.
5. Hidden/protected-field checks at API, search, export and AI-context boundaries.
6. Duplicate provisioning, concurrent seat-cap invites, bounced reminders, outbox retry/dead-letter, expired sessions, re-authentication, unavailable sources, partial retrieval, conflicting evidence, stale approvals, configuration release without adoption and credential rotation.
7. Browser desktop/mobile, keyboard, screen-reader, contrast, reduced-motion and nonblank error-fallback checks across the complete route inventory.

## 4. Release decision

**NO-GO** is required at this checkpoint because the acceptance rule says any absent critical security/isolation or production evidence must not be inferred from local tests. No critical failure was observed in the local automated run, but absence of external proof is itself a release blocker.

## 5. Pending activities

- Complete three-tenant authenticated lifecycle evidence and retain redacted API/audit traces.
- Execute route-by-route cross-tenant checks for records, search, export, attachments, workers, caches and AI context.
- Prove field/action policy behavior for visible, read-only, hidden and protected fields.
- Capture browser screenshots and keyboard/screen-reader evidence for platform admin, customer admin, investigator, quality and approver journeys.
- Validate production-like cookie/session revocation across multiple application instances.
- Execute real SMTP/Resend delivery, bounce handling and inbound webhook deduplication/replay tests.
- Execute live GenAI provider validation with assurance and limitation evidence, if enabled for the design partner.
- Validate production object storage, attachment lifecycle, malware scanning and tenant quotas.
- Run production connector health/schema checks with real endpoint credentials.
- Run hosted GitHub CI and retain the workflow run URL and artifacts.
- Repeat affected gates after any failure, then update this report to GO only when all mandatory evidence passes.

## 6. Reproduction commands used

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp="$env:TEMP\mdarix-part08-full"
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -m compileall -q backend briefs scenario_intelligence source_simulator integration reports
.\.venv\Scripts\python.exe -m alembic current
docker compose config --quiet
Invoke-RestMethod http://127.0.0.1:8007/health
Invoke-RestMethod http://127.0.0.1:8101/health
Invoke-RestMethod http://127.0.0.1:8102/health
Invoke-RestMethod http://127.0.0.1:8103/health
Invoke-RestMethod http://127.0.0.1:8104/health
```
