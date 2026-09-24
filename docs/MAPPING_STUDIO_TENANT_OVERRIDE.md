# Mapping Studio — Tenant Overrides

Tenant administrators may override permitted mapping rows for their tenant version. Platform-only fields, tenant identity, provenance, audit identity, and canonical protected fields are rejected server-side. Overrides are tenant-scoped, durable, and audited.

Master releases preserve existing tenant versions and overrides; impact history is append-only and retained for later review.
