from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    node_id: str
    entity_type: str
    canonical_entity_id: str
    tenant_id: str
    display_label: str
    status: str | None = None
    quality_state: str | None = None
    source_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphRelationship(BaseModel):
    id: str
    type: str
    source_node: str
    target_node: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    assertion_type: str
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    recorded_at: datetime | None = None
    quality_status: str | None = None
    evidence_count: int = 0
    provenance_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    relationships: list[GraphRelationship]
    metadata: dict[str, Any]


class RelationshipDetail(BaseModel):
    relationship: GraphRelationship
    provenance: list[dict[str, Any]]
    evidence: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    database: str
