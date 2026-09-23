# Stage 2 — Plans, subscriptions and usage

The platform-admin API exposes the plan catalog, tenant subscription, effective plan entitlements, usage counters and limit alerts. Plan and subscription changes are authenticated platform-admin operations and produce enterprise audit events. Contractual limit changes are platform-admin-only; customer administrators cannot self-grant capacity.

Effective entitlement provenance is explicit: `PLAN`, `TENANT_OVERRIDE`, or `PLATFORM_OVERRIDE`. Current schema stores plan feature limits in `feature_entitlements`; tenant-specific extension remains a versioned migration item where a separate override record is required.

Endpoints: `GET/POST /api/v1/platform-admin/plans`, `GET /api/v1/platform-admin/customers/{tenant_id}/subscription`, and `GET /api/v1/platform-admin/customers/{tenant_id}/usage`.
