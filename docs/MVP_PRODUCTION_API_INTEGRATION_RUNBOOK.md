# MDARIX R1 production-like API integration runbook

## What is implemented

MDARIX keeps provider data outside the MDARIX database and reads it through a tenant-scoped API connector. The local contract uses four isolated services:

| Provider | API | Database | Default token |
|---|---:|---|---|
| TrackWise | `http://127.0.0.1:8101` | `trackwise-simulator-db` | `sim-a` |
| PLM | `http://127.0.0.1:8102` | `plm-simulator-db` | `sim-a` |
| ERP | `http://127.0.0.1:8103` | `erp-simulator-db` | `sim-a` |
| Supplier | `http://127.0.0.1:8104` | `supplier-simulator-db` | `sim-a` |

Each provider validates its token and tenant key. Source records and history remain in the provider database. MDARIX only receives authorized records through the connector and queues tenant-scoped outbox events.

## Connector configuration contract

Persist only metadata, never a token or password:

```json
{
  "endpoint": "https://customer-provider.example/api",
  "health_path": "health",
  "schema_path": "schema/Complaint",
  "records_path": "records/Complaint",
  "source_object": "Complaint",
  "tenant_key": "CUSTOMER_A",
  "credential_ref": "CUSTOMER_A_TRACKWISE_TOKEN",
  "mapping_version": "TRACKWISE_COMPLAINT_TO_MDARIX_COMPLAINT@1.0",
  "timeout_seconds": 10
}
```

The referenced secret must be supplied by the deployment secret manager/environment. Production connector calls reject loopback, private, link-local, reserved, and multicast destinations; local simulator URLs are allowed only in development. Response sizes and timeouts are bounded.

## Local verification

1. Start PostgreSQL and the four simulator databases/API services with `docker compose up -d postgres trackwise-simulator-db trackwise-simulator plm-simulator-db plm-simulator erp-simulator-db erp-simulator supplier-simulator-db supplier-simulator`.
2. Verify each provider `/health` and `/ready` endpoint.
3. Verify a tenant-scoped read with `X-Provider-Token` and `tenant=TENANT_A`; repeat with `TENANT_B` and confirm records differ.
4. Sign in as a platform administrator and create a connector using the metadata above. Store the token only as `CUSTOMER_A_TRACKWISE_TOKEN`.
5. Run provider health, schema discovery, then activate the connector only after review and mapping validation.
6. Execute the connector. Confirm the response tenant matches the authenticated tenant and that outbox events are queued.
7. Run the outbox worker and verify retry/dead-letter behavior using the simulator fault profile.

## Customer deployment checklist

For each customer provider, obtain the approved base URL, authentication scheme, secret reference, health/schema routes, pagination and cursor rules, rate-limit contract, retry semantics, idempotency key, error mapping, mapping version, ownership, retention, and residency requirements. Validate these in a staging environment before activation. Do not use a customer database password in MDARIX configuration; prefer the customer’s API or a separately deployed adapter.

## Current external gates

Real customer endpoints and credentials, provider-specific contract responses, production secret-manager integration, production object storage, production PostgreSQL/TLS/backup/monitoring, multi-instance deployment, and hosted CI remain operational validations. They cannot be truthfully marked complete from this workstation.
