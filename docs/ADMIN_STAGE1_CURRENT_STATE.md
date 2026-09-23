# Platform Admin Stage 1 — Current State

## Existing capability

- Authenticated administrator context supplies the display name, role, and tenant.
- Administrator navigation is role-gated and separate from customer business-data views.
- Customer administrator invitation, search, email update, retirement, reactivation,
  session-safe invitation tokens, and audit history are available.
- Customer provisioning APIs create a tenant, plan assignment, and limit metadata.
- Frontend build and backend regression are available through the repository gates.

## Classification

| Area | Classification | Notes |
|---|---|---|
| Admin shell and role gate | KEEP + REFACTOR | Preserve authenticated boundary; extend navigation. |
| Customer administrator invite/manage | KEEP + REFACTOR | Preserve passwordless invitation and audit behavior. |
| Customer provisioning API | REUSE | Add wizard and Customer 360 presentation. |
| Raw metric/admin API responses | REUSE | Present through typed cards and tables. |
| Customer business-data access | DEPRECATE | Never grant platform-admin data bypass. |
| Three-screen-only navigation | REMOVE AFTER REPLACEMENT | Replace with Stage 1 information architecture. |

