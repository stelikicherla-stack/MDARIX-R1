# MDARIX database schema reference

## Scope

The canonical schema is defined by the Alembic migrations under
`infrastructure/database/migrations/versions`. SQLAlchemy models are loaded by
`backend/app/db/base.py`. This makes migrations the deployment source of truth;
models describe runtime access.

## Tenant and identity boundary

Tenant-owned tables carry `tenant_id` and are protected by the database RLS
policy created by `ab44dbhardening`. Composite tenant-safe foreign keys are used
for cross-entity relationships where practical. `auth_users`, durable sessions,
memberships, roles, permissions, plans, mappings, evidence, decisions, reports,
outbox events, and audit events are tenant-scoped.

## Core groups

| Group | Representative tables | Purpose |
|---|---|---|
| Identity | `auth_users`, `auth_sessions`, `tenant_memberships`, `role_definitions`, `role_assignments` | Identity, sessions, tenant roles and access |
| Product | `products`, `product_versions`, `components`, `suppliers`, `sites`, `lots` | Product reality and configuration |
| Investigation | `investigations`, `decisions`, `investigation_briefs`, `context_snapshots` | Review and governed decisions |
| Evidence | `evidence`, evidence chunks/links, attachments | Source material and provenance |
| Integration | connector configurations, mappings, outbox/inbound events | Provider exchange and replay safety |
| Governance | `audit_events`, `signed_approval_records`, policies | Immutable evidence, signatures and authorization |

## Important database controls

- RLS is enabled and forced on tenant-owned tables.
- Audit events are append-only through `audit_events_immutable`.
- Composite foreign keys prevent cross-tenant relationships.
- Tenant and time indexes support the primary retrieval and audit paths.
- Runtime pool sizing is controlled by `MDARIX_DB_POOL_SIZE`,
  `MDARIX_DB_MAX_OVERFLOW`, and `MDARIX_DB_POOL_TIMEOUT_SECONDS`.

## Operational verification

Run `python scripts/validate_db_hardening.py` after applying migrations. Review
`alembic history`, `pg_indexes`, `pg_policies`, and the trigger definition before
each production release. Production TLS, backup encryption, and restore proof
must be recorded separately; they are not implied by the schema.
