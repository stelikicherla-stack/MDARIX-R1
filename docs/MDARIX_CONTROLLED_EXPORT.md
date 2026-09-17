# Controlled Export — Day 25 foundation

`backend.app.controlled_export.prepare_export` applies authorization, tenant
matching, a maximum-record operating limit, an explicit authorized-field set,
and secret/token/password exclusion before producing export rows.

Focused tests cover authorized filtering, hidden-field omission, cross-tenant
denial, anonymous/unauthorized denial, and oversized scope blocking. Export
audit persistence and a complete API surface remain open Day 25 work.
