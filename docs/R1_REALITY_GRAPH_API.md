# MDARIX R1 Reality Graph API

## Base

`/api/v1/graph`

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Application/database readiness |
| GET | `/api/v1/graph/nodes/{entity_type}/{id}` | Node lookup |
| GET | `/api/v1/graph/nodes/{entity_type}/{id}/neighbors` | Bounded neighborhood |
| GET | `/api/v1/graph/products/{product_id}` | Product graph |
| GET | `/api/v1/graph/investigations/{investigation_id}` | Investigation graph |
| GET | `/api/v1/graph/relationships/{relationship_id}` | Relationship detail, provenance, evidence |
| GET | `/api/v1/graph/paths` | Bounded relationship path |

## Parameters

Neighborhood parameters:

- `depth`: 0-3
- `direction`: `both`, `in`, or `out`
- `relationship_type`: optional controlled relationship type
- `target_entity_type`: optional supported node type

Path parameters:

- `source_type`
- `source_id`
- `target_type`
- `target_id`
- `max_depth`: 0-5

## Response Shape

Graph responses include:

- `nodes`
- `relationships`
- `metadata`

Relationship details include:

- `relationship`
- `provenance`
- `evidence`

## Errors

Safe structured errors are returned for invalid entity type, invalid relationship type, invalid depth, node not found, relationship not found, and path not found.

## Limits

Traversal is bounded and does not expose arbitrary SQL or graph-query execution.

## Important Semantics

Graph path does not mean causal path.
