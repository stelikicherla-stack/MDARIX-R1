# Evidence UX Specification

Evidence resolution order is investigation evidence, selected ProductVersion evidence, then the tenant library. Cards show classification (Supporting, Contradicting, Contextual, Unresolved, Missing), source, reliability, ProductVersion, temporal relevance, hypothesis relationship, and document reference.

The endpoint `/api/v1/analytics/evidence` is tenant-scoped and read-only. Missing metadata is rendered as “not recorded.” Evidence does not become a conclusion without authorized interpretation.
