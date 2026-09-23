# Story View Specification

Story View is the connected executive/auditor traceability view. It presents the full Product-to-Decision chain, with filters for ProductVersion, time mode, investigation, evidence classification, and status. It exposes known, unknown, contradicted, missing, and late-arriving states and carries provenance into exports.

`/api/v1/story/{investigation_id}` returns a tenant-scoped traceability skeleton and never discloses whether a foreign investigation exists.
