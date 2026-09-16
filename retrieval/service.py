import datetime as dt
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import case, func, or_, text
from sqlalchemy.orm import Session

from backend.app.db.models.evidence_intelligence import EvidenceChunk, EvidenceEntityLink, EvidenceObservation
from backend.app.db.models.foundation import (
    Component,
    ComponentSupplier,
    Complaint,
    Evidence,
    InvestigationEvidence,
    LotBatch,
    LotComponent,
    Product,
    ProductComponent,
    ProductSupplier,
    ProductVersion,
    Supplier,
)
from backend.app.db.models.retrieval_intelligence import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_PIPELINE_VERSION,
    RETRIEVAL_CONFIG_VERSION,
    EvidenceChunkEmbedding,
    RetrievalQuery,
)
from retrieval.embedding_provider import DeterministicEmbeddingProvider, vector_literal
from retrieval.schemas import RetrievalRequest, RetrievalResponse, RetrievalResult


class RetrievalError(Exception):
    pass


class TrustedRetrievalService:
    def __init__(self, embedding_provider: DeterministicEmbeddingProvider | None = None):
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()

    def index_evidence_chunks(self, db: Session, tenant_id: uuid.UUID, reprocess: bool = False) -> dict[str, Any]:
        metadata = self.embedding_provider.model_metadata()
        chunks = (
            db.query(EvidenceChunk)
            .join(Evidence, Evidence.id == EvidenceChunk.evidence_id)
            .filter(EvidenceChunk.tenant_id == tenant_id, Evidence.tenant_id == tenant_id)
            .filter(~func.lower(Evidence.evidence_identifier).like("%ground_truth%"))
            .order_by(EvidenceChunk.evidence_id, EvidenceChunk.sequence_number)
            .all()
        )
        indexed = 0
        skipped = 0
        failed = 0

        for chunk in chunks:
            existing = (
                db.query(EvidenceChunkEmbedding)
                .filter(
                    EvidenceChunkEmbedding.tenant_id == tenant_id,
                    EvidenceChunkEmbedding.chunk_id == chunk.id,
                    EvidenceChunkEmbedding.chunk_checksum == chunk.checksum,
                    EvidenceChunkEmbedding.embedding_model == metadata.model,
                    EvidenceChunkEmbedding.model_version == metadata.model_version,
                    EvidenceChunkEmbedding.pipeline_version == metadata.pipeline_version,
                )
                .first()
            )
            if existing and not reprocess:
                skipped += 1
                continue
            if existing and reprocess:
                db.delete(existing)
                db.flush()

            try:
                vector = self.embedding_provider.embed_text(chunk.text_content)
                row = EvidenceChunkEmbedding(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    evidence_id=chunk.evidence_id,
                    chunk_id=chunk.id,
                    chunk_checksum=chunk.checksum or "",
                    provider=metadata.provider,
                    embedding_model=metadata.model,
                    model_version=metadata.model_version,
                    embedding_dimension=metadata.dimension,
                    pipeline_version=metadata.pipeline_version,
                    distance_metric=metadata.distance_metric,
                    embedding=vector_literal(vector),
                    indexing_status="INDEXED",
                )
                indexed += 1
            except Exception as exc:
                row = EvidenceChunkEmbedding(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    evidence_id=chunk.evidence_id,
                    chunk_id=chunk.id,
                    chunk_checksum=chunk.checksum or "",
                    provider=metadata.provider,
                    embedding_model=metadata.model,
                    model_version=metadata.model_version,
                    embedding_dimension=metadata.dimension,
                    pipeline_version=metadata.pipeline_version,
                    distance_metric=metadata.distance_metric,
                    embedding=None,
                    indexing_status="FAILED",
                    failure_reason=str(exc),
                )
                failed += 1
            db.add(row)

        db.commit()
        return {
            "chunks_seen": len(chunks),
            "indexed": indexed,
            "skipped": skipped,
            "failed": failed,
            "embedding_model": metadata.model,
            "embedding_dimension": metadata.dimension,
            "pipeline_version": metadata.pipeline_version,
        }

    def retrieve(self, db: Session, request: RetrievalRequest) -> RetrievalResponse:
        if request.tenant_id is None:
            raise RetrievalError("tenant_id is required for trusted retrieval")

        query_vector = self.embedding_provider.embed_text(request.query_text)
        structured = self._structured_candidates(db, request) if request.retrieval_mode in {"structured", "hybrid"} else {}
        semantic = self._semantic_candidates(db, request, query_vector) if request.retrieval_mode in {"semantic", "hybrid"} else {}

        merged = self._merge_candidates(structured, semantic)
        results = [self._materialize_result(db, request, candidate) for candidate in merged]
        results = [r for r in results if r is not None]
        results.sort(key=lambda item: item.retrieval_score, reverse=True)
        results = results[: request.top_k]

        status = "COMPLETED"
        limitations: list[str] = []
        if not results:
            status = "NO_RELEVANT_EVIDENCE"
            limitations.append("No relevant tenant-scoped, context-valid evidence was retrieved.")
        elif max(r.retrieval_score for r in results) < 0.15:
            status = "INSUFFICIENT_RELEVANT_EVIDENCE"
            limitations.append("Retrieved evidence did not meet the minimum relevance threshold.")

        provenance = RetrievalQuery(
            id=uuid.uuid4(),
            tenant_id=request.tenant_id,
            investigation_id=request.investigation_id,
            query_text=request.query_text,
            retrieval_mode=request.retrieval_mode,
            temporal_mode=request.temporal_mode,
            filters=self._filter_payload(request),
            embedding_model=EMBEDDING_MODEL,
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            retrieval_config_version=RETRIEVAL_CONFIG_VERSION,
            top_k=request.top_k,
            returned_refs=[
                {
                    "evidence_id": str(result.evidence_id),
                    "chunk_id": str(result.chunk_id),
                    "retrieval_score": result.retrieval_score,
                    "retrieval_method": result.retrieval_method,
                }
                for result in results
            ],
            status=status,
        )
        db.add(provenance)
        db.commit()

        return RetrievalResponse(
            retrieval_query_id=provenance.id,
            status=status,
            query_text=request.query_text,
            retrieval_mode=request.retrieval_mode,
            temporal_mode=request.temporal_mode,
            top_k=request.top_k,
            results_count=len(results),
            results=results,
            limitations=limitations,
        )

    def _base_query(self, db: Session, request: RetrievalRequest):
        q = (
            db.query(EvidenceChunk, Evidence)
            .join(Evidence, Evidence.id == EvidenceChunk.evidence_id)
            .filter(EvidenceChunk.tenant_id == request.tenant_id, Evidence.tenant_id == request.tenant_id)
        )
        if request.evidence_types:
            q = q.filter(Evidence.evidence_type.in_(request.evidence_types))
        if request.date_from:
            q = q.filter(or_(Evidence.effective_timestamp >= request.date_from, Evidence.ingestion_timestamp >= request.date_from))
        if request.date_to:
            q = q.filter(or_(Evidence.effective_timestamp <= request.date_to, Evidence.ingestion_timestamp <= request.date_to))
        q = self._apply_temporal(q, request)
        q = self._apply_lifecycle_filters(q, request)
        return q

    def _apply_temporal(self, q, request: RetrievalRequest):
        if request.temporal_mode == "event" and request.event_as_of:
            q = q.filter(or_(Evidence.effective_timestamp.is_(None), Evidence.effective_timestamp <= request.event_as_of))
        if request.temporal_mode == "known" and request.knowledge_as_of:
            q = q.filter(Evidence.ingestion_timestamp.is_not(None), Evidence.ingestion_timestamp <= request.knowledge_as_of)
        return q

    def _apply_lifecycle_filters(self, q, request: RetrievalRequest):
        entity_filters = {
            "Product": request.product_id,
            "ProductVersion": request.product_version_id,
            "Component": request.component_id,
            "Supplier": request.supplier_id,
            "LotBatch": request.lot_id,
            "Complaint": request.complaint_id,
        }
        for entity_type, entity_id in entity_filters.items():
            if entity_id:
                q = q.filter(
                    Evidence.id.in_(
                        self._evidence_ids_for_entity_filter(request.tenant_id, entity_type, entity_id)
                    )
                )
        if request.investigation_id:
            q = q.filter(
                or_(
                    Evidence.investigation_id == request.investigation_id,
                    Evidence.id.in_(self._investigation_evidence_ids(request.tenant_id, request.investigation_id)),
                )
            )
        return q

    def _evidence_ids_for_entity_filter(self, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID):
        return (
            text(
                "SELECT evidence_id FROM evidence_entity_links "
                "WHERE tenant_id=:tenant_id AND entity_type=:entity_type AND entity_id=:entity_id"
            )
            .bindparams(tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id)
            .columns(evidence_id=Evidence.id.type)
        )

    def _investigation_evidence_ids(self, tenant_id: uuid.UUID, investigation_id: uuid.UUID):
        return (
            text("SELECT evidence_id FROM investigation_evidence WHERE tenant_id=:tenant_id AND investigation_id=:investigation_id")
            .bindparams(tenant_id=tenant_id, investigation_id=investigation_id)
            .columns(evidence_id=Evidence.id.type)
        )

    def _structured_candidates(self, db: Session, request: RetrievalRequest) -> dict[uuid.UUID, dict[str, Any]]:
        candidates: dict[uuid.UUID, dict[str, Any]] = {}
        rows = self._base_query(db, request).all()
        query_terms = {term.lower() for term in request.query_text.split() if len(term) > 2}
        for chunk, evidence in rows:
            reasons = self._structured_reasons(db, request, evidence, chunk)
            text_terms = f"{evidence.title} {chunk.text_content}".lower()
            term_hits = sum(1 for term in query_terms if term in text_terms)
            score = min(0.85, 0.35 + 0.1 * len(reasons) + 0.05 * term_hits)
            candidates[chunk.id] = {
                "chunk_id": chunk.id,
                "score": score,
                "methods": {"structured"},
                "reasons": reasons or ["tenant-scoped evidence candidate"],
            }
        return candidates

    def _semantic_candidates(self, db: Session, request: RetrievalRequest, query_vector: list[float]) -> dict[uuid.UUID, dict[str, Any]]:
        vector = vector_literal(query_vector)
        filters = ["ec.tenant_id = :tenant_id", "emb.indexing_status = 'INDEXED'"]
        params: dict[str, Any] = {"tenant_id": request.tenant_id, "query_vector": vector, "limit": max(request.top_k * 4, 20)}
        if request.evidence_types:
            filters.append("e.evidence_type = ANY(:evidence_types)")
            params["evidence_types"] = request.evidence_types
        if request.temporal_mode == "event" and request.event_as_of:
            filters.append("(e.effective_timestamp IS NULL OR e.effective_timestamp <= :event_as_of)")
            params["event_as_of"] = request.event_as_of
        if request.temporal_mode == "known" and request.knowledge_as_of:
            filters.append("(e.ingestion_timestamp IS NOT NULL AND e.ingestion_timestamp <= :knowledge_as_of)")
            params["knowledge_as_of"] = request.knowledge_as_of
        sql = text(
            "SELECT ec.id AS chunk_id, 1 - (emb.embedding <=> (:query_vector)::vector) AS score "
            "FROM evidence_chunk_embeddings emb "
            "JOIN evidence_chunks ec ON ec.tenant_id=emb.tenant_id AND ec.id=emb.chunk_id "
            "JOIN evidence e ON e.tenant_id=ec.tenant_id AND e.id=ec.evidence_id "
            f"WHERE {' AND '.join(filters)} "
            "ORDER BY emb.embedding <=> (:query_vector)::vector LIMIT :limit"
        )
        rows = db.execute(sql, params).all()
        raw = {
            row.chunk_id: {
                "chunk_id": row.chunk_id,
                "score": max(float(row.score or 0.0), 0.0),
                "methods": {"semantic"},
                "reasons": ["semantic match"],
            }
            for row in rows
        }
        return self._context_filter_candidate_ids(db, request, raw)

    def _context_filter_candidate_ids(self, db: Session, request: RetrievalRequest, candidates: dict[uuid.UUID, dict[str, Any]]):
        if not candidates:
            return candidates
        allowed_rows = self._base_query(db, request).filter(EvidenceChunk.id.in_(list(candidates))).all()
        allowed = {chunk.id for chunk, _ in allowed_rows}
        return {chunk_id: data for chunk_id, data in candidates.items() if chunk_id in allowed}

    def _merge_candidates(self, structured: dict[uuid.UUID, dict[str, Any]], semantic: dict[uuid.UUID, dict[str, Any]]) -> list[dict[str, Any]]:
        merged = dict(structured)
        for chunk_id, item in semantic.items():
            if chunk_id in merged:
                merged[chunk_id]["score"] = min(1.0, max(merged[chunk_id]["score"], item["score"]) + 0.1)
                merged[chunk_id]["methods"].update(item["methods"])
                merged[chunk_id]["reasons"] = sorted(set(merged[chunk_id]["reasons"] + item["reasons"]))
            else:
                merged[chunk_id] = item
        for item in merged.values():
            item["method"] = "hybrid" if len(item["methods"]) > 1 else next(iter(item["methods"]))
        return sorted(merged.values(), key=lambda item: item["score"], reverse=True)

    def _materialize_result(self, db: Session, request: RetrievalRequest, candidate: dict[str, Any]) -> RetrievalResult | None:
        row = (
            db.query(EvidenceChunk, Evidence)
            .join(Evidence, Evidence.id == EvidenceChunk.evidence_id)
            .filter(EvidenceChunk.tenant_id == request.tenant_id, Evidence.tenant_id == request.tenant_id, EvidenceChunk.id == candidate["chunk_id"])
            .first()
        )
        if not row:
            return None
        chunk, evidence = row
        links = (
            db.query(EvidenceEntityLink)
            .filter(EvidenceEntityLink.tenant_id == request.tenant_id, EvidenceEntityLink.evidence_id == evidence.id)
            .all()
        )
        observations = (
            db.query(EvidenceObservation)
            .filter(EvidenceObservation.tenant_id == request.tenant_id, EvidenceObservation.evidence_id == evidence.id)
            .all()
        )
        temporal_context = {
            "effective_timestamp": evidence.effective_timestamp.isoformat() if evidence.effective_timestamp else None,
            "recorded_timestamp": evidence.recorded_timestamp.isoformat() if evidence.recorded_timestamp else None,
            "ingestion_timestamp": evidence.ingestion_timestamp.isoformat() if evidence.ingestion_timestamp else None,
            "temporal_mode": request.temporal_mode,
        }
        return RetrievalResult(
            result_id=f"{evidence.id}:{chunk.id}",
            evidence_id=evidence.id,
            evidence_identifier=evidence.evidence_identifier,
            evidence_type=evidence.evidence_type,
            evidence_title=evidence.title,
            chunk_id=chunk.id,
            chunk_sequence_number=chunk.sequence_number,
            source_anchor=chunk.source_anchor or {},
            excerpt=(chunk.source_anchor or {}).get("excerpt") or chunk.text_content[:240],
            retrieval_method=candidate["method"],
            retrieval_score=round(float(candidate["score"]), 6),
            structured_match_reasons=candidate["reasons"],
            related_entities=[
                {
                    "entity_type": link.entity_type,
                    "entity_id": str(link.entity_id) if link.entity_id else None,
                    "raw_reference": link.raw_reference,
                    "resolution_status": link.resolution_status,
                }
                for link in links
            ],
            temporal_context=temporal_context,
            evidence_available=self._is_available(evidence, request),
            quality_limitations=[
                limitation.get("description", str(limitation))
                for obs in observations
                for limitation in (obs.limitations or [])
                if isinstance(limitation, dict)
            ],
            provenance={
                "embedding_model": EMBEDDING_MODEL,
                "embedding_model_version": EMBEDDING_MODEL_VERSION,
                "embedding_dimension": EMBEDDING_DIMENSION,
                "embedding_pipeline_version": EMBEDDING_PIPELINE_VERSION,
                "retrieval_config_version": RETRIEVAL_CONFIG_VERSION,
                "retrieval_score_semantics": "retrieval relevance only; not truth, confidence, evidence strength, or causality",
            },
        )

    def _is_available(self, evidence: Evidence, request: RetrievalRequest) -> bool:
        if request.temporal_mode != "known" or not request.knowledge_as_of:
            return True
        return evidence.ingestion_timestamp is not None and evidence.ingestion_timestamp <= request.knowledge_as_of

    def _structured_reasons(self, db: Session, request: RetrievalRequest, evidence: Evidence, chunk: EvidenceChunk) -> list[str]:
        reasons = ["tenant match"]
        requested = [
            ("Product", request.product_id),
            ("ProductVersion", request.product_version_id),
            ("Component", request.component_id),
            ("Supplier", request.supplier_id),
            ("LotBatch", request.lot_id),
            ("Complaint", request.complaint_id),
        ]
        links = (
            db.query(EvidenceEntityLink)
            .filter(EvidenceEntityLink.tenant_id == request.tenant_id, EvidenceEntityLink.evidence_id == evidence.id)
            .all()
        )
        linked = {(link.entity_type, link.entity_id) for link in links}
        for entity_type, entity_id in requested:
            if entity_id and (entity_type, entity_id) in linked:
                reasons.append(f"{entity_type} filter match")
        if request.investigation_id and evidence.investigation_id == request.investigation_id:
            reasons.append("investigation evidence match")
        if request.temporal_mode == "known" and request.knowledge_as_of:
            reasons.append("available before knowledge_as_of")
        if request.temporal_mode == "event" and request.event_as_of:
            reasons.append("effective before event_as_of")
        if chunk.source_anchor:
            reasons.append("source anchor present")
        return reasons

    def _filter_payload(self, request: RetrievalRequest) -> dict[str, Any]:
        payload = request.model_dump(mode="json")
        payload.pop("query_text", None)
        payload.pop("tenant_id", None)
        return payload
