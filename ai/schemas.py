from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SourceAnchorSchema(BaseModel):
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    section_heading: Optional[str] = Field(None, description="Section heading or title")
    paragraph_index: Optional[int] = Field(None, description="0-indexed paragraph number")
    row_identifier: Optional[str] = Field(None, description="Row identifier for structured data")
    character_range: Optional[List[int]] = Field(None, description="Start and end char offset [start, end]")
    excerpt: Optional[str] = Field(None, description="Minimal verbatim source excerpt")


class EntityLinkCandidateSchema(BaseModel):
    raw_reference: str = Field(..., description="Raw text reference in the document")
    entity_type: str = Field(
        ...,
        description="Type: Product, ProductVersion, Component, Supplier, ManufacturingSite, LotBatch, Requirement, Change, Complaint, Investigation, Risk, FailureMode, Control",
    )
    candidate_identifier: Optional[str] = Field(None, description="Candidate ID (e.g. PRD-001, CMP-REV-B)")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class ExtractedObservationSchema(BaseModel):
    statement: str = Field(..., description="Observation statement extracted directly from source")
    observation_type: str = Field(
        "AI_EXTRACTED_OBSERVATION",
        description="EXPLICIT_SOURCE_STATEMENT, STRUCTURED_EXTRACTION, DETERMINISTIC_DERIVATION, AI_EXTRACTED_OBSERVATION",
    )
    source_anchor: SourceAnchorSchema = Field(..., description="Source anchor locating the statement in evidence")
    related_entity_references: List[EntityLinkCandidateSchema] = Field(default_factory=list)
    effective_context: Optional[dict[str, Any]] = Field(None, description="Event or temporal context extracted")
    limitations: List[str] = Field(default_factory=list, description="Limitations explicitly noted or detected")


class LimitationSchema(BaseModel):
    limitation_type: str = Field(..., description="e.g. missing_lot_traceability, unclear_version, unknown_date")
    description: str = Field(...)


class EvidenceExtractionResult(BaseModel):
    evidence_id: str = Field(..., description="MDARIX evidence UUID or identifier")
    title: Optional[str] = Field(None)
    document_date: Optional[str] = Field(None, description="Extracted ISO date if present")
    observations: List[ExtractedObservationSchema] = Field(default_factory=list)
    entity_candidates: List[EntityLinkCandidateSchema] = Field(default_factory=list)
    limitations: List[LimitationSchema] = Field(default_factory=list)
    candidate_conflicts: List[str] = Field(default_factory=list)
    extraction_status: str = Field("COMPLETED", description="COMPLETED, COMPLETED_WITH_LIMITATIONS, EXTRACTION_FAILED")
    warnings: List[str] = Field(default_factory=list)
