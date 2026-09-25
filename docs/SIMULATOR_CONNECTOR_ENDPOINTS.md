# Simulator Connector Endpoint Contract

The local provider simulators expose production-shaped HTTP contracts on the
following host ports. The four services use separate PostgreSQL databases and
must be configured as separate connector instances.

| Provider | Base URL | Database | Provider token |
| --- | --- | --- | --- |
| TrackWise | `http://127.0.0.1:8101` | `trackwise` | `sim-a` / `sim-b` / `sim-c` / `sim-d` |
| PLM | `http://127.0.0.1:8102` | `plm` | `sim-a` / `sim-b` / `sim-c` / `sim-d` |
| ERP | `http://127.0.0.1:8103` | `erp` | `sim-a` / `sim-b` / `sim-c` / `sim-d` |
| Supplier | `http://127.0.0.1:8104` | `supplier` | `sim-a` / `sim-b` / `sim-c` / `sim-d` |

## Endpoint contract

Each persistent simulator provides:

- `GET /health` - liveness and provider identity.
- `GET /ready` - readiness including isolated database availability.
- `GET /schema/{entity}?tenant=TENANT_A` - versioned source-field schema.
- `GET /records/{entity}?tenant=TENANT_A` - tenant-scoped current records.
- `GET /records/{entity}/{external_id}/history?tenant=TENANT_A` - record history.
- `POST /records/{entity}?tenant=TENANT_A` - controlled simulator write for test setup only.

All protected routes require `X-Provider-Token`. The token is mapped to one
tenant and a requested tenant outside that token's scope returns `403`.

The simulator uses deterministic cursor-ready record contracts and durable
record history. The MDARIX connector must still implement the production
controls below rather than assuming the simulator is proof of customer
integration:

| Required connector property | Simulator/test value |
| --- | --- |
| Endpoint URL | Provider base URL above; never a tenant-supplied authority |
| Authentication scheme | `X-Provider-Token` in local tests; replace with provider-specific auth in production |
| Credential reference | Server-side secret name, for example `MDARIX_TRACKWISE_TOKEN`; never persist the token |
| Health route | `/health` |
| Readiness route | `/ready` |
| Schema route | `/schema/{entity}` |
| Pagination | Implement connector cursor/page handling; the legacy deterministic simulator record route is the current-page contract |
| Incremental cursor | Use provider record version/history or a provider-specific timestamp cursor; do not infer it from tenant IDs |
| Rate limits | Treat `429` as retryable with bounded backoff and `Retry-After` support |
| Retry semantics | Retry network errors and `5xx`; do not retry authentication, authorization, validation, or schema errors blindly |
| Idempotency key | `(tenant_id, provider, entity, external_id, record_version, mapping_version)` |
| Error mapping | Preserve sanitized provider status/code and map to connector-run failure categories |
| Mapping version | Pin every ingestion run to an immutable master/tenant mapping version |
| Data ownership/retention | Keep source provenance, tenant scope, retention class, and deletion policy with each staged record |

## PowerShell verification

```powershell
$providerChecks = @(
  @{ Name = "TRACKWISE"; Base = "http://127.0.0.1:8101" },
  @{ Name = "PLM";       Base = "http://127.0.0.1:8102" },
  @{ Name = "ERP";       Base = "http://127.0.0.1:8103" },
  @{ Name = "SUPPLIER";  Base = "http://127.0.0.1:8104" }
)

foreach ($provider in $providerChecks) {
  $health = Invoke-RestMethod "$($provider.Base)/health"
  $ready = Invoke-RestMethod "$($provider.Base)/ready"
  if ($health.status -ne "ok" -or $ready.status -ne "ready") {
    throw "$($provider.Name) health/readiness failed"
  }
  Write-Host "PASS $($provider.Name): health and readiness"
}

$headers = @{ "X-Provider-Token" = "sim-a" }
Invoke-RestMethod "http://127.0.0.1:8101/schema/Complaint?tenant=TENANT_A" -Headers $headers
Invoke-RestMethod "http://127.0.0.1:8101/records/Complaint?tenant=TENANT_A" -Headers $headers

try {
  Invoke-RestMethod "http://127.0.0.1:8101/records/Complaint?tenant=TENANT_B" -Headers $headers
  throw "FAIL: provider token crossed tenant scope"
}
catch {
  if ([int]$_.Exception.Response.StatusCode -ne 403) { throw }
  Write-Host "PASS TrackWise: cross-tenant provider scope denied"
}
```

## Manual production setup

For each customer provider, an administrator must supply and approve:

1. Base endpoint and environment (test/staging/production).
2. Authentication scheme and a vault secret reference.
3. Health, readiness, schema, and record routes.
4. Pagination and incremental-cursor documentation.
5. Rate-limit and retry guidance.
6. Idempotency and external-ID rules.
7. Source-to-canonical mapping version and required-field policy.
8. Data owner, retention, deletion, residency, and attachment rules.
9. A non-production credential for health/schema testing.
10. Approval evidence before activation; credentials must never be entered into Git, browser payloads, audit details, or mapping records.

Simulator health and records prove only the connector contract. They do not
prove real customer connectivity, provider credentials, production rate
limits, production schema stability, or customer retention obligations.
