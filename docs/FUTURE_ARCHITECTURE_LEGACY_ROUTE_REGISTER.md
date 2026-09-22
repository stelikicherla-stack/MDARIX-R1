# MDARIX R1 Future Architecture — Legacy Route Register

Status: **Stage 1 register; no route removed in this audit**

| Route family | Current behavior | Classification | Required owner/action |
|---|---|---|---|
| `/api/v1/products*` | Product360/timeline use service/default tenant paths; audit can label anonymous actor. | REFACTOR / P0 | Stage 2 shared context and explicit tenant parameter. |
| `/api/v1/graph*` | Graph service has hardcoded synthetic tenant; routes do not require auth. | REFACTOR / P0 | Stage 2 protect and tenant-scope graph queries. |
| `/api/v1/evidence*` | Cookie is used when present, but absent cookie falls back to default tenant. | REFACTOR / P0 | Remove fallback; require authenticated context. |
| `/api/v1/retrieval*` | Index/query use default tenant and do not receive request identity. | REFACTOR / P0 | Context dependency; tenant filter before vector retrieval. |
| `/api/v1/investigations*` | Workspace, analysis, and hypotheses use default tenant helper. | REFACTOR / P0 | Context dependency and composite parent/child checks. |
| `/api/v1/investigations/*/briefs*` | Historical fallback uses `SYSTEM` and default tenant when no session. | REFACTOR / P0 | Require actor and tenant; preserve immutable snapshot. |
| `/api/v1/investigations/*/decisions*` | Decision routes use default tenant and lack uniform actor handling. | REFACTOR / P0 | Context, approval authority, SoD, and authenticated actor. |
| `/api/v1/trust*` | Assurance routes use default tenant without uniform auth. | REFACTOR / P0 | Context and tenant-isolated execution lookup. |
| `/api/v1/evaluation*` | Evaluation routes use default tenant and create persistence records. | REFACTOR / P0 | Restrict to authorized operators and durable evaluation identity. |
| `/api/v1/counterfactuals*` | Uses default tenant helper. | REFACTOR / P0 | Context and read/write audit separation. |
| `/api/v1/integration/preview` | Preview path has historically accepted client tenant input. | REFACTOR / P0 | Derive tenant server-side; validate mapping ownership. |
| `/api/v1/ask*`, Challenger, Failure Chain, Scenario | Newer authenticated, tenant-aware controlled paths. | KEEP + HARDEN | Use shared context and align audit contract. |
| `/api/v1/admin*` | Authenticated admin checks exist; broad role strings and generic patch path remain. | KEEP + HARDEN | Split platform/customer admin scopes and typed commands. |
| `/api/v1/auth*` | Durable users but in-memory sessions/tokens; unsafe cookie default. | REFACTOR / P0 | Durable auth session/token model and secure deployment profile. |

## Duplicate implementation register

| Concern | Duplicate paths | Consolidation rule |
|---|---|---|
| Tenant resolution | `get_default_tenant_id`, hardcoded service tenants, authenticated context helpers | Only request context may establish user tenant. |
| Authentication | `auth.service` memory state plus database `AuthUser` | Database-backed identity/session/token model. |
| Authorization | role-string checks, route-local checks, frontend visibility | Server permission evaluator is authoritative; UI mirrors it. |
| Audit | enterprise helper plus direct `AuditEvent` construction | One audited command/event contract with recursive redaction. |
| Retrieval | default-tenant retrieval routes and authenticated Ask/workspace retrieval | One tenant-filtered retrieval service. |
| Admin updates | resource-specific routes plus generic dynamic patch | Typed resource commands; deprecate generic patch after migration. |
