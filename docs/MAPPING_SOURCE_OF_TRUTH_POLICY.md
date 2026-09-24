# MDARIX R1 — Source-of-Truth Policy

Source authority is explicit: `AUTHORITATIVE`, `REFERENCE`, `SUPPLEMENTARY`, or `OBSERVED_SOURCE_VALUE`. MDARIX preserves all source values and provenance; it does not silently overwrite conflicting values. A source payload cannot set tenant, actor, authorization, audit, or internal canonical identity.

Conflicts remain visible for review. Mapping and normalization are versioned, auditable, and tenant isolated.
