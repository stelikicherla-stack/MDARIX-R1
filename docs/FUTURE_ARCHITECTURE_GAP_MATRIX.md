# MDARIX R1 Future Architecture — Gap Matrix

| Capability | Current implementation | Target architecture | Risk | Priority | Action | Stage | Status |
|---|---|---|---|---|---|---|---|
| Authenticated request context | Mixed cookie parsing and default tenant fallbacks | One required context dependency | Cross-tenant/anonymous access | P0 | Implement and apply to every tenant-owned route | 2 | OPEN |
| Tenant isolation | Good service filters in newer paths; legacy defaults/hardcoded tenant remain | Server-derived tenant across SQL, graph, vector, files, jobs, audit | Data disclosure | P0 | Route and service audit with adversarial tests | 2 | OPEN |
| Durable sessions/tokens | In-memory sessions, activation, reset tokens | Durable hashed AuthSession/Invitation/Reset records | Restart/multi-worker invalidation | P0 | Add tables, revocation, expiry, replay controls | 2 | OPEN |
| Cookie/security profile | HttpOnly/SameSite present; `secure=False` hardcoded | Environment-enforced Secure cookie and startup checks | Session theft | P0 | Fail unsafe production configuration | 2 | OPEN |
| Invitation/email delivery | Synchronous SMTP, development-token fallback | Provider abstraction + transactional outbox + Resend | Account-state divergence | P0 | Add provider/outbox/delivery state | 2 | PARTIAL |
| Product/Investigation/Evidence route protection | New routes protected; legacy routes not uniform | All customer-owned APIs require context | Unauthorized reads/writes | P0 | Consolidate legacy route families | 2 | OPEN |
| Case Context | Browser carries scattered selection state | Persisted validated `MDARIXCaseContext` | Stale/mismatched investigation story | P0 | Implement context cascade/versioning | 2 | MISSING |
| Identity/membership | AuthUser and memberships exist; one-tenant assumptions remain | Global identity with tenant memberships/roles | Incorrect multi-tenant administration | P0 | Normalize membership-driven authorization | 2 | PARTIAL |
| Governed object audit | Append-only trigger and operational events | Field-level immutable object history and transaction coupling | Non-reproducible regulated history | P1 | Extend existing audit framework | 2/4 | PARTIAL |
| Admin separation | Platform/customer concepts exist; UI/API scope is inconsistent | Separate platform and customer admin capabilities | Privilege escalation | P1 | Explicit permission matrix and tests | 2/4 | PARTIAL |
| Connector platform | Deterministic FILE/REST/DATABASE contracts | Provider abstraction, secrets, retry, health, reconciliation | False production readiness | P1 | Implement one real safe adapter and health surface | 2/3 | PARTIAL |
| Mapping 2.0 | Master/tenant mapping models and previews exist | Versioned canonical/source model with activation and rollback | Customer-specific code drift | P1 | Add lifecycle, compatibility, and approval gates | 2 | PARTIAL |
| GenAI/model provider | Deterministic local engines and embeddings | Governed ModelProvider with safe context and evaluation | MVP capability misrepresentation | P1 | Add provider seam; label deterministic mode | 3 | PARTIAL |
| Controlled agents | Logical service engines, no autonomous authority | Agent/Tool/Policy/Execution records and deny-by-default writes | Unauthorized AI action | P1 | Implement controlled agent contract | 3/4 | PARTIAL |
| Dashboards/analytics | UI surfaces exist; no unified AnalyticsService | Server-backed tenant-aware analytics APIs | Disconnected customer experience | P1 | Build primary command/product/investigation dashboards | 3 | PARTIAL |
| Reports | Brief/report concepts exist | Permissioned interactive/export report framework | Weak design-partner value | P1 | Deliver primary consolidated report | 3/4 | PARTIAL |
| Frontend quality | 976-line monolith, no frontend tests | Feature modules, typed API client, React tests, browser E2E | Regression/accessibility risk | P1 | Extract incrementally; add test gates | 3/4 | OPEN |
| CI/release | No workflows; manual validation | CI for backend/frontend/migrations/security | Unrepeatable release claims | P1 | Add GitHub Actions and evidence artifacts | 4 | MISSING |
| Dependency pinning | Frontend manifest uses `latest`; lockfile exists | Pinned compatible versions | Reproducibility failure | P1 | Pin dependencies and update intentionally | 4 | OPEN |
| Backup/restore/export/privacy | Documentation/partial foundation | Controlled tested operations | Data-loss/privacy risk | P1 | Add MVP-safe backup/export/privacy gates | 4 | OPEN |
| Future domain packs | Medical device concepts dominate | Shared regulated-product core + domain packs | Costly Pharma/Life Sciences expansion | FUTURE | Preserve abstractions; defer entities | 3+ | ARCHITECTURE READY |
