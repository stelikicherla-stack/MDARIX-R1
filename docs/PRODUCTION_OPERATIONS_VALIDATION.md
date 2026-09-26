# Production operations validation

The repository provides the code-side controls for liveness/readiness probes,
a dedicated transactional-outbox worker, worker retry/dead-letter handling,
and tenant-scoped operational health APIs. Production evidence requires the
deployment itself.

## Health gate

Set a comma-separated list of deployed application URLs and run:

```powershell
$env:MDARIX_OPERATIONAL_URLS = "https://mdarix-app-1.example,https://mdarix-app-2.example"
python scripts/validate_production_operations.py
```

The gate requires HTTP 200 from `/health/live` and `/health/ready` on every
target. Two distinct URLs are required before multi-instance health is shown
as PASS.

## Monitoring and alerts

Configure `MDARIX_MONITORING_ALERT_WEBHOOK` to the approved PagerDuty,
Opsgenie, Teams, or equivalent alert receiver. Configure
`MDARIX_OUTBOX_ALERT_WEBHOOK` separately for dead-letter alerts. Do not place
credentials in this document or source control. The worker emits structured
heartbeat/retry/dead-letter logs; production monitoring must scrape those logs
and retain alert delivery evidence.

The worker also supports `MDARIX_OUTBOX_HEARTBEAT_FILE`, an atomic JSON
heartbeat file suitable for a sidecar, Prometheus textfile collector, or host
monitor. The file contains only timestamps and counters, never event payloads.

## Honest release status

Local readiness is not production validation. The following remain PENDING
until evidence is captured from deployed infrastructure: alert delivery,
worker heartbeat monitoring, two-instance session/revocation behavior,
database-backed readiness on each instance, and operational incident routing.
