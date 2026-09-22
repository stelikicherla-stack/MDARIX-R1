# MDARIX R1 — Stage 1 Architecture, Security and Future-State Freeze Report

Date: 2026-09-22

Status: **STAGE 1 COMPLETE AS AN AUDIT/FREEZE DELIVERABLE; MVP NO-GO PENDING P0 REMEDIATION**

## 1. Scope executed

The attached Master Prompt Stage 1 scope was executed as a read-only repository audit. The review covered environment prerequisites, repository structure, backend/frontend architecture, identity and tenancy, route protection, data model/migrations, integration/mapping, intelligence services, admin controls, tests, documentation, and delivery tooling.

Required Stage 1 artifacts:

- `FUTURE_ARCHITECTURE_CURRENT_STATE.md`
- `FUTURE_ARCHITECTURE_GAP_MATRIX.md`
- `FUTURE_ARCHITECTURE_SECURITY_FINDINGS.md`
- `FUTURE_ARCHITECTURE_TARGET_BLUEPRINT.md`
- `FUTURE_ARCHITECTURE_LEGACY_ROUTE_REGISTER.md`

## 2. Environment evidence

| Check | Result |
|---|---|
| Git branch | `main` |
| `HEAD` vs `origin/main` | Equal at audit checkpoint: `42736b4ce1a33fb772ac6c71d2100fa9c918bd0e` |
| Node | Available: `v24.15.0` |
| npm | Installed, but PowerShell script execution policy blocked `npm.ps1`; use `npm.cmd` after policy review. |
| Controlled Python 3.13 venv | **BLOCKED**: `.venv\Scripts\python.exe` could not execute because its referenced interpreter is inaccessible. |
| Active Python | Available globally as `3.14.4`, not the required controlled 3.13.x. |
| Docker/Desktop | **BLOCKED**: `docker` was not found on PATH; Docker context, compose, PostgreSQL, pgvector, and health could not be independently verified in this shell. |
| Migrations | Migration files are present through `p32_reusable_offboarded_emails.py`; `alembic current/heads/history` was not run because the controlled environment was unavailable. |
| Worktree | Not clean; existing uncommitted auth/email/access/frontend changes and generated test artifacts were preserved. |

No destructive migration or external-system change was performed.

## 3. Major findings

1. The project has meaningful regulated-product domain depth and a coherent evidence-bounded intelligence direction.
2. The security model is split: newer Ask/admin/intelligence paths use authenticated context, while multiple legacy tenant-owned routes fall back to a synthetic tenant or hardcoded tenant.
3. This is a P0 issue. Test counts and local reports cannot establish MVP readiness while an unauthenticated HTTP boundary can reach customer-owned data or mutation services.
4. Authentication persistence is not production-ready because sessions and invitation/reset tokens are process memory.
5. The current deterministic intelligence engines are safe R1 scaffolding, not yet a production GenAI/agent platform; the product and reports must state that accurately.
6. Frontend functionality is broad but concentrated in a 976-line monolith with no frontend test files, while API contracts are not centralized.
7. Delivery is manual: no active CI, no backend/frontend production container definitions, uncontrolled frontend `latest` dependencies, and significant scratch-file pollution.

## 4. Stage 1 classification

- **KEEP:** PostgreSQL/pgvector, canonical regulated-product model, evidence/provenance/temporal concepts, modular monolith, controlled intelligence services, mapping abstraction.
- **KEEP + HARDEN:** authenticated Ask/admin/intelligence routes, governance/approval concepts, append-only audit trigger, connector contracts.
- **REFACTOR:** request context, legacy routes, auth/session/token persistence, admin patch/update commands, audit contract, frontend composition.
- **TEST/DEMO ONLY until qualified:** deterministic provider claims and VS001–VS012 deferred evidence.
- **REMOVE AFTER REPLACEMENT:** synthetic anonymous tenant fallback and generated test artifacts from source control.

## 5. MVP direction

Freeze broad feature expansion. Build one design-partner workflow as a secure vertical slice:

`Login → Product → ProductVersion → complaint/signal → Investigation → Evidence → Ask MDARIX → bounded intelligence → Decision Brief → human reauthentication/approval → AI Assurance → Case Audit Timeline → report`.

The MVP should be sold as a read-only intelligence layer over customer systems of record, with controlled writes only to MDARIX-owned workflow records. External write-back, autonomous regulatory conclusions, and broad domain-pack implementation remain out of scope.

## 6. Stage 2 entry gates

Stage 2 may begin only with the following explicit work items:

- one `AuthenticatedRequestContext` applied to every customer-owned route;
- no anonymous/default-tenant fallback;
- durable sessions, invitation/reset tokens, revocation, and replay protection;
- secure production cookie configuration;
- persisted Case Context with Product/ProductVersion/Investigation cascade validation;
- transactional outbox and provider-neutral email abstraction;
- adversarial tenant tests covering Product, ProductVersion, Complaint, Investigation, Evidence, Graph, Retrieval, Decision, Mapping, Attachment, and Report;
- migration/runtime verification under controlled Python 3.13 and Docker/pgvector;
- explicit documentation of deterministic R1 intelligence versus future GenAI.

## 7. Final Stage 1 recommendation

**MVP DESIGN-PARTNER NO-GO** at this checkpoint.

Reason: P0 route authentication/tenant-boundary defects and unavailable controlled runtime evidence prevent a defensible MVP readiness claim. This is an audit disposition, not a rejection of the product direction. The existing domain foundation is suitable for continued work after the P0 gates are closed.

## 8. Unresolved items

- Docker and PostgreSQL/pgvector runtime verification.
- Controlled Python 3.13 environment repair/recreation.
- Alembic current/head/history verification.
- P0 legacy-route protection and adversarial proof.
- Durable auth/session/token design.
- Durable case context.
- Resend/provider abstraction and transactional outbox.
- Frontend test and CI foundation.
- Final VS001–VS012 qualification, intentionally deferred by the existing R1 decision.
