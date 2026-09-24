# MDARIX R1 — Canonical Data Model

The canonical lifecycle model is tenant-scoped and uses stable internal UUIDs. MVP entities are Product, ProductVersion, Component, Supplier, Site, Lot, Complaint, Investigation, Evidence, Risk, FailureMode, Control, CAPA, VigilanceAssessment, and FieldAction.

Every source record retains `source_application`, `source_object`, `source_record_key`, connector/version, source created/updated/event/known timestamps, and a canonical link. Canonical relationships are descriptive and provenance-backed; they do not imply causality.

System-managed identity, tenant, provenance, audit, authorization, and mapping-version fields are platform controlled.
