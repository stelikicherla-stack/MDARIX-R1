from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    id: str
    product_identifier: str
    name: str
    product_family: str | None
    lifecycle_status: str
    available_versions: list[str]


class TimelineEvent(BaseModel):
    event_id: str
    event_type: str
    category: str
    title: str
    description: str | None = None
    related_entity_type: str
    related_entity_id: str
    event_time: datetime | None = None
    effective_time: datetime | None = None
    recorded_time: datetime | None = None
    knowledge_available_time: datetime | None = None
    source: str | None = None
    quality_status: str | None = None
    provenance_available: bool = True
    evidence_available: bool = False
    late_arriving: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class Product360Response(BaseModel):
    product: dict[str, Any]
    selected_version: dict[str, Any] | None
    versions: list[dict[str, Any]]
    overview: dict[str, Any]
    configuration: dict[str, Any]
    changes: list[dict[str, Any]]
    manufacturing: dict[str, Any]
    complaints: list[dict[str, Any]]
    investigations: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    failure_modes: list[dict[str, Any]]
    controls: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    limitations: list[dict[str, Any]]
    provenance: list[dict[str, Any]]
    timeline: list[TimelineEvent]
    temporal_context: dict[str, Any]
    metadata: dict[str, Any]


class TemporalRealityResponse(BaseModel):
    product_id: str
    product_version_id: str | None = None
    mode: str
    as_of: datetime | None = None
    events: list[TimelineEvent]
    event_count: int
    late_arriving_count: int
    metadata: dict[str, Any]
