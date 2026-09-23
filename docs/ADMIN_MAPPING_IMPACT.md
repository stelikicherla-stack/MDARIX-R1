# Stage 2 — Mapping impact and release controls

Before release, mapping impact metadata identifies the source system, canonical target, affected version and tenant overrides. Silent propagation is prohibited: a master release does not change an existing tenant activation. The controlled sequence is `review -> validation -> approval -> activation`, with a new tenant mapping version where required. Transformation rules are declarative/versioned; arbitrary executable code is not accepted.

`GET /api/v1/platform-admin/mapping-impact` exposes the release rule and immutable-release indicator for platform review.
