# Stage 2 — Canonical data model

`GET /api/v1/platform-admin/canonical-model` returns the controlled catalog of governed entities, including products, versions, suppliers, sites, complaints, investigations, evidence, intelligence, decisions, approvals, provenance and audit. The endpoint is metadata-only and explicitly rejects the idea of a raw schema editor. New entity types can be added to the catalog without exposing database structure.
