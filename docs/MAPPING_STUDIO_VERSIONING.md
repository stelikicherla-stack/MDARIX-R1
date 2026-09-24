# Mapping Studio — Versioning

Master mappings are platform-owned. Tenant mapping versions are durable, tenant-scoped records with explicit lifecycle states: `DRAFT`, `VALIDATION`, `READY_FOR_APPROVAL`, `APPROVED`, `RELEASED`, `SUPERSEDED`, and `RETIRED`.

Released versions are immutable. A new master release does not mutate an active tenant version; it requires impact review and a new tenant draft. Status transitions and approvals are authenticated and audited.

## Evidence

The API exposes persisted mapping versions, lifecycle status changes, version comparison, and impact history. Platform administrators alone can create or release master mappings.
