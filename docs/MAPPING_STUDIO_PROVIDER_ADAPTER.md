# Mapping Studio Provider Adapter

Connector configurations can now define a provider endpoint without storing a
credential in the database:

```json
{
  "endpoint": "https://provider.example/api",
  "health_path": "health",
  "schema_path": "schema",
  "credential_ref": "MDARIX_TRACKWISE_TOKEN",
  "schema_version": "v1",
  "timeout_seconds": 5
}
```

Authenticated platform administrators can call:

- `POST /api/v1/admin/configuration/connectors/{id}/provider-health`
- `POST /api/v1/admin/configuration/connectors/{id}/discover-schema`

The adapter uses a bounded timeout, returns sanitized provider errors, never
returns authorization headers or credentials, records an administrative audit
event, and never automatically applies discovered schema changes. A real
provider result requires a reachable endpoint and a runtime secret referenced
by `credential_ref`; no provider credential is committed to the repository.
