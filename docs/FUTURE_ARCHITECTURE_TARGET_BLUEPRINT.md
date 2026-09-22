# MDARIX R1 Future Architecture — Target Blueprint

## Architectural decision

Keep MDARIX as a modular monolith for MVP. Do not add microservices, Kafka, Neo4j, OpenSearch, Redis, Kubernetes, or a lakehouse until a measured requirement exists. Use explicit interfaces so those technologies can be added later.

## Trusted request and case context

Create one server-side `AuthenticatedRequestContext` dependency containing:

`user_id`, `session_id`, `tenant_id`, `membership_id`, `active_role_id`, `persona`, `permission_set_ids`, `plan_id`, `entitlements`, and `correlation_id`.

Create one persisted `MDARIXCaseContext` per user/tenant workspace containing Product, ProductVersion, signal/complaint scope, investigation, temporal mode/cutoff, brief, decision, context version, and last page. Every selection is validated against the authenticated membership and compatible parent scope. A product/version switch clears incompatible downstream selections instead of leaving stale state in the browser.

## Platform boundaries

- Identity: global user identity → tenant membership → tenant role → permissions.
- Regulated core: Product/RegulatedProduct and ProductVersion/RegulatedVersion remain the current canonical anchors; future pharmaceutical and life-science packs add domain entities without duplicating the platform core.
- Evidence: source facts, derived observations, AI interpretations, hypotheses, contradictions, unknowns, limitations, and human decisions remain distinct.
- Intelligence: SQL + temporal + graph + vector retrieval, with tenant filtering before model context construction.
- Trust: provenance, prompt governance, model/provider version, evaluation, causal restraint, and human authority are mandatory output metadata.
- Integration: connector definitions → source objects/fields → master mappings → tenant mappings/overrides → controlled ingestion/reconciliation.
- Notifications: provider abstraction with Resend as the future provider; outbound and inbound email must be tenant/case resolved, verified, audited, and never trusted automatically as evidence.
- Storage: PostgreSQL/pgvector for metadata and indexes; object storage abstraction for large evidence and report artifacts.

## Transaction and audit rules

Use a PostgreSQL transactional outbox for domain events and notifications. Every material governed change and every intelligence execution carries tenant, authenticated actor, correlation, context snapshot, provenance, and outcome. Mandatory audit persistence is part of the governed transaction. Read-only intelligence creates execution/access events, not source-object mutation events.

## MVP product slice

The first design-partner slice is one 10–15 minute investigation story:

External/synthetic source → declarative mapping → Product → ProductVersion → complaint/signal scope → Investigation → Evidence → Ask MDARIX → hypotheses/challenges/unknowns → human-reviewed Decision Brief → reauthentication/approval → AI Assurance → Case Audit Timeline → consolidated report.

The product should explicitly label deterministic R1 intelligence versus future GenAI. Controlled agents may retrieve, compare, summarize, and recommend next steps, but cannot approve, reject, declare root cause, write external systems, or modify approved records.

## Stage ordering

1. Stage 2: request context, durable auth/tokens, tenant boundary, case context, outbox, and route consolidation.
2. Stage 3: connected story UX, governed model provider, controlled agents, dashboards, reports, and admin separation.
3. Stage 4: adversarial security, browser E2E, qualification evidence, golden journey, and MVP decision.
