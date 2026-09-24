# Mapping Studio — Dry Run

Dry run accepts a sample/test record set and mapping rules, applies the preview transformation contract, and returns source/target records without writing canonical business data. The response is explicitly non-persistent and includes record counts.

Release is blocked by missing required targets, protected-field violations, invalid transformations, incompatible schema, or unresolved validation errors. Production provider payloads must be treated as untrusted data and never as tenant authority.
