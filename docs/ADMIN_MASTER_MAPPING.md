# Stage 2 — Master Mapping Studio

Master mappings define connector-to-canonical relationships. Tenant mapping versions and field overrides are separate records, tenant-scoped, auditable and lifecycle-controlled. The lifecycle is `DRAFT`, `VALIDATION`, `READY_FOR_APPROVAL`, `APPROVED`, `RELEASED`, `SUPERSEDED`, `RETIRED`; released versions are immutable.

Protected platform fields include tenant ownership, audit identifiers, provenance identifiers, source identity and security fields. They cannot be overridden by customer mapping rules.
