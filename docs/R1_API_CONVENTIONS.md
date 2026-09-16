# MDARIX R1 API Conventions

## Status

PROPOSED for Day 1 architecture freeze.

## Baseline

- REST
- JSON
- `/api/v1/`

## Resource Naming

Use plural kebab-case resource names:

- `/products`
- `/product-versions`
- `/components`
- `/suppliers`
- `/lots`
- `/complaints`
- `/investigations`
- `/evidence`
- `/hypotheses`
- `/unknowns`
- `/failure-chains`
- `/scenarios`
- `/decisions`
- `/ai-executions`

## IDs

Use opaque UUID-style IDs at the API boundary. Do not expose source-system primary keys as canonical MDARIX IDs.

## Timestamps

Use ISO 8601 UTC timestamps. Temporal fields must be semantically named, such as `event_timestamp`, `effective_timestamp`, `recorded_timestamp`, `ingestion_timestamp`, `ai_execution_timestamp`, and `decision_timestamp`.

## Pagination, Filtering, Sorting

Use `page`, `page_size`, `sort`, and typed filter parameters. Cursor pagination may be introduced for high-volume evidence and timeline streams.

## Tenant and Audit Context

Every request is resolved under tenant context and carries correlation/request IDs. Mutating requests must emit audit events.

## Errors

Error responses include `code`, `message`, `details`, `correlation_id`, and `timestamp`. Do not leak secrets or hidden model internals.

## Versioning

R1 starts with `/api/v1/`. Breaking changes require a new API version or explicit compatibility layer.

## Day 1 Boundary

This document defines conventions only. It does not implement endpoints.
