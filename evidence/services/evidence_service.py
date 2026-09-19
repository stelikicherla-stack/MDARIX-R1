import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ai.extractor import AIEvidenceExtractor
from backend.app.db.models.evidence_intelligence import (
    EvidenceChunk,
    EvidenceEntityLink,
    EvidenceObservation,
    EvidencePropositionRelation,
)
from backend.app.db.models.foundation import AIExecution, Evidence
from evidence.extractors.chunker import EvidenceChunker
from evidence.extractors.deterministic_extractor import DeterministicExtractor
from evidence.extractors.entity_linker import EntityLinker
from evidence.extractors.grounding_validator import GroundingValidator
from evidence.services.content_reader import EvidenceContentReader

logger = logging.getLogger(__name__)


def build_evidence_summary(evidence: Evidence, observations: list[EvidenceObservation], tenant_id: uuid.UUID) -> Dict[str, Any]:
    """Build a typed, non-inferential summary for frontend and brief consumers."""
    source = {"id": str(evidence.id), "identifier": evidence.evidence_identifier, "title": evidence.title, "fact_type": evidence.fact_type}
    return {
        "facts": [o.statement for o in observations if o.observation_type == "EXPLICIT_SOURCE_STATEMENT"],
        "source_evidence": [source],
        "derived_observations": [o.statement for o in observations if o.observation_type != "EXPLICIT_SOURCE_STATEMENT"],
        "supporting_evidence": [],
        "contradictory_evidence": [],
        "unresolved_evidence": [o.statement for o in observations if o.quality_status != "VALIDATED"],
        "missing_evidence": [],
        "unknowns": [],
        "limitations": [limitation for o in observations for limitation in (o.limitations or [])],
        "provenance": {"tenant_id": str(tenant_id), "evidence_id": str(evidence.id), "source_system": evidence.source_system, "source_reference": evidence.source_reference, "source_timestamp": evidence.source_timestamp.isoformat() if evidence.source_timestamp else None, "ingestion_timestamp": evidence.ingestion_timestamp.isoformat() if evidence.ingestion_timestamp else None},
        "sufficiency": "SUFFICIENT_FOR_REVIEW" if observations and not any(o.quality_status != "VALIDATED" for o in observations) else "PARTIALLY_SUFFICIENT" if observations else "INSUFFICIENT",
        "temporal_context": {"mode": "current", "as_of": None},
    }


class EvidenceIntelligenceService:
    """Core orchestrator for Evidence Intelligence processing, extraction, linking, and grounding."""

    def __init__(self):
        self.content_reader = EvidenceContentReader()
        self.chunker = EvidenceChunker()
        self.deterministic_extractor = DeterministicExtractor()
        self.ai_extractor = AIEvidenceExtractor()
        self.entity_linker = EntityLinker()
        self.grounding_validator = GroundingValidator()

    def process_evidence_intelligence(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        evidence_id: uuid.UUID,
        reprocess: bool = False,
    ) -> Dict[str, Any]:
        """Runs full evidence intelligence pipeline for a specific evidence record idempotently."""

        evidence = (
            db.query(Evidence)
            .filter(Evidence.tenant_id == tenant_id, Evidence.id == evidence_id)
            .first()
        )
        if not evidence:
            raise ValueError(f"Evidence record {evidence_id} not found for tenant {tenant_id}")

        # Idempotency check: if already processed and not forced reprocess, return existing summary
        if not reprocess:
            existing_obs = (
                db.query(EvidenceObservation)
                .filter(EvidenceObservation.tenant_id == tenant_id, EvidenceObservation.evidence_id == evidence_id)
                .count()
            )
            if existing_obs > 0:
                return self.get_evidence_intelligence_summary(db, tenant_id, evidence_id)

        # 1. Access Content
        content, metadata = self.content_reader.get_evidence_content(db, tenant_id, evidence_id)

        # Clear existing extracted records in child-first order if reprocessing
        obs_ids = [o.id for o in db.query(EvidenceObservation.id).filter(EvidenceObservation.tenant_id == tenant_id, EvidenceObservation.evidence_id == evidence_id).all()]
        if obs_ids:
            db.query(EvidencePropositionRelation).filter(EvidencePropositionRelation.tenant_id == tenant_id, EvidencePropositionRelation.observation_id.in_(obs_ids)).delete(synchronize_session=False)
        db.query(EvidenceEntityLink).filter(EvidenceEntityLink.tenant_id == tenant_id, EvidenceEntityLink.evidence_id == evidence_id).delete(synchronize_session=False)
        db.query(EvidenceObservation).filter(EvidenceObservation.tenant_id == tenant_id, EvidenceObservation.evidence_id == evidence_id).delete(synchronize_session=False)
        db.flush()


        # 2. Chunk Evidence
        chunks = self.chunker.create_chunks_for_evidence(db, tenant_id, evidence_id, content, metadata)


        # 3. Deterministic Extraction
        det_observations = self.deterministic_extractor.extract_deterministic_observations(
            db, tenant_id, evidence_id, content, metadata
        )

        # 4. Narrative AI Extraction & AIExecution Provenance Logging
        ai_result, ai_execution_id = self.ai_extractor.extract_evidence(
            db, tenant_id, evidence_id, evidence.title, content, metadata
        )

        # 5. Grounding Validation
        validated_result = self.grounding_validator.validate_extraction(ai_result, content)

        # 6. Persist Validated AI Observations
        ai_obs_records: List[EvidenceObservation] = []
        for obs_schema in validated_result.observations:
            # Map chunk
            matching_chunk = chunks[0] if chunks else None
            anchor_dict = obs_schema.source_anchor.model_dump() if obs_schema.source_anchor else {}

            obs_rec = EvidenceObservation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                chunk_id=matching_chunk.id if matching_chunk else None,
                statement=obs_schema.statement,
                observation_type=obs_schema.observation_type,
                extraction_method="GENAI",
                source_anchor=anchor_dict,
                quality_status="VALIDATED" if not validated_result.warnings else "LIMITATIONS",
                limitations=[l.model_dump() for l in validated_result.limitations] if validated_result.limitations else None,
                ai_execution_id=ai_execution_id,
            )
            db.add(obs_rec)
            db.flush()
            ai_obs_records.append(obs_rec)


            # Link entities for this observation
            if obs_schema.related_entity_references:
                self.entity_linker.resolve_and_link_entities(
                    db=db,
                    tenant_id=tenant_id,
                    evidence_id=evidence_id,
                    observation_id=obs_rec.id,
                    candidates=obs_schema.related_entity_references,
                )

        # 7. Link candidate entities overall
        if validated_result.entity_candidates:
            self.entity_linker.resolve_and_link_entities(
                db=db,
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                observation_id=None,
                candidates=validated_result.entity_candidates,
            )

        db.commit()
        return self.get_evidence_intelligence_summary(db, tenant_id, evidence_id)

    def associate_proposition_relation(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        observation_id: uuid.UUID,
        proposition_text: str,
        relation_type: str,  # SUPPORT, CONTRADICT, NEUTRAL_CONTEXTUAL
        rationale: Optional[str] = None,
    ) -> EvidencePropositionRelation:
        """Associates an extracted evidence observation with an explicit proposition (SUPPORT / CONTRADICT / NEUTRAL_CONTEXTUAL)."""
        relation = EvidencePropositionRelation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            observation_id=observation_id,
            proposition_text=proposition_text,
            relation_type=relation_type,
            rationale=rationale,
        )
        db.add(relation)
        db.commit()
        return relation

    def get_evidence_intelligence_summary(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Queries evidence record, chunks, observations, entity links, and AI provenance."""
        evidence = (
            db.query(Evidence)
            .filter(Evidence.tenant_id == tenant_id, Evidence.id == evidence_id)
            .first()
        )
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found")

        chunks = (
            db.query(EvidenceChunk)
            .filter(EvidenceChunk.tenant_id == tenant_id, EvidenceChunk.evidence_id == evidence_id)
            .order_by(EvidenceChunk.sequence_number)
            .all()
        )

        observations = (
            db.query(EvidenceObservation)
            .filter(EvidenceObservation.tenant_id == tenant_id, EvidenceObservation.evidence_id == evidence_id)
            .all()
        )

        entity_links = (
            db.query(EvidenceEntityLink)
            .filter(EvidenceEntityLink.tenant_id == tenant_id, EvidenceEntityLink.evidence_id == evidence_id)
            .all()
        )

        ai_executions = (
            db.query(AIExecution)
            .filter(
                AIExecution.tenant_id == tenant_id,
                AIExecution.evidence_refs["evidence_id"].astext == str(evidence_id),
            )
            .all()
        )

        return {
            "evidence": {
                "id": str(evidence.id),
                "evidence_identifier": evidence.evidence_identifier,
                "evidence_type": evidence.evidence_type,
                "title": evidence.title,
                "source_system": evidence.source_system,
                "document_ref": evidence.document_ref,
                "reliability_status": evidence.reliability_status,
                "fact_type": evidence.fact_type,
                "effective_timestamp": evidence.effective_timestamp.isoformat() if evidence.effective_timestamp else None,
                "ingestion_timestamp": evidence.ingestion_timestamp.isoformat() if evidence.ingestion_timestamp else None,
            },
            "evidence_summary": build_evidence_summary(evidence, observations, tenant_id),
            "chunks_count": len(chunks),
            "chunks": [
                {
                    "id": str(c.id),
                    "sequence_number": c.sequence_number,
                    "text_content": c.text_content,
                    "source_anchor": c.source_anchor,
                    "checksum": c.checksum,
                }
                for c in chunks
            ],
            "observations_count": len(observations),
            "observations": [
                {
                    "id": str(o.id),
                    "statement": o.statement,
                    "observation_type": o.observation_type,
                    "extraction_method": o.extraction_method,
                    "source_anchor": o.source_anchor,
                    "quality_status": o.quality_status,
                    "limitations": o.limitations,
                    "ai_execution_id": str(o.ai_execution_id) if o.ai_execution_id else None,
                }
                for o in observations
            ],
            "entity_links_count": len(entity_links),
            "entity_links": [
                {
                    "id": str(el.id),
                    "entity_type": el.entity_type,
                    "entity_id": str(el.entity_id) if el.entity_id else None,
                    "raw_reference": el.raw_reference,
                    "resolution_status": el.resolution_status,
                }
                for el in entity_links
            ],
            "ai_provenance_count": len(ai_executions),
            "ai_provenance": [
                {
                    "id": str(ex.id),
                    "provider": ex.provider,
                    "model_name": ex.model_name,
                    "prompt_template_version": ex.prompt_template_version,
                    "validation_status": ex.validation_status,
                    "execution_timestamp": ex.execution_timestamp.isoformat() if ex.execution_timestamp else None,
                }
                for ex in ai_executions
            ],
        }
