# Operational health — Day 25 checkpoint

`/health/live` reports only process liveness. `/health/ready` performs a safe
database readiness check. The existing `/health` remains the minimal database
health contract. No credentials, connection strings, tokens, or stack traces
are returned. Dependency-specific health and correlation middleware remain
follow-up work.
