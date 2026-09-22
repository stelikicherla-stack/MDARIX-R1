# Stage 2 — Tenancy

Tenant-owned workspace context is keyed by `(tenant_id, user_id)`, and scope validation checks Product, ProductVersion, and Investigation ownership before persistence. The same boundary must be propagated to graph, search, vector, files, jobs, exports, mappings, connectors, reports, notifications, and AI context during router consolidation.
