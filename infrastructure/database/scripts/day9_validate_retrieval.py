import datetime as dt
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import text

from backend.app.db.models.foundation import Product, ProductVersion, Tenant
from backend.app.db.models.retrieval_intelligence import EMBEDDING_DIMENSION, EMBEDDING_MODEL, EvidenceChunkEmbedding, RetrievalQuery
from backend.app.db.session import SessionLocal
from retrieval.schemas import RetrievalRequest
from retrieval.service import TrustedRetrievalService


def run_day9_validation() -> int:
    print("=" * 72)
    print("STARTING DAY 9 TRUSTED EVIDENCE RETRIEVAL VALIDATION")
    print("=" * 72)

    db = SessionLocal()
    errors: list[str] = []

    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_key == "ACME_CARE_SYNTHETIC").first() or db.query(Tenant).first()
        if not tenant:
            print("[FAIL] No tenant available.")
            return 1
        print(f"[PASS] Tenant scope verified ({tenant.tenant_key})")

        ext = db.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar()
        if not ext:
            errors.append("pgvector extension is not installed.")
            print("[FAIL] pgvector extension missing.")
        else:
            print(f"[PASS] pgvector operational ({ext})")

        service = TrustedRetrievalService()
        index_summary = service.index_evidence_chunks(db, tenant.id)
        if index_summary["chunks_seen"] == 0:
            errors.append("No EvidenceChunk records available for indexing.")
            print("[FAIL] No EvidenceChunk records available.")
        else:
            print(f"[PASS] EvidenceChunk indexing checked ({index_summary})")

        indexed = (
            db.query(EvidenceChunkEmbedding)
            .filter(EvidenceChunkEmbedding.tenant_id == tenant.id, EvidenceChunkEmbedding.indexing_status == "INDEXED")
            .count()
        )
        if indexed == 0:
            errors.append("No indexed chunk embeddings found.")
            print("[FAIL] No indexed embeddings found.")
        else:
            print(f"[PASS] Embedding persistence/provenance present ({indexed} indexed rows).")

        bad_dimension = (
            db.query(EvidenceChunkEmbedding)
            .filter(EvidenceChunkEmbedding.tenant_id == tenant.id, EvidenceChunkEmbedding.embedding_dimension != EMBEDDING_DIMENSION)
            .count()
        )
        if bad_dimension:
            errors.append("Embedding dimension mismatch detected.")
            print("[FAIL] Embedding dimension mismatch.")
        else:
            print(f"[PASS] Embedding model/dimension explicit ({EMBEDDING_MODEL}, {EMBEDDING_DIMENSION}).")

        before = db.query(EvidenceChunkEmbedding).filter(EvidenceChunkEmbedding.tenant_id == tenant.id).count()
        second_summary = service.index_evidence_chunks(db, tenant.id)
        after = db.query(EvidenceChunkEmbedding).filter(EvidenceChunkEmbedding.tenant_id == tenant.id).count()
        if before != after:
            errors.append("Embedding indexing is not idempotent.")
            print("[FAIL] Embedding idempotency failed.")
        else:
            print(f"[PASS] Embedding idempotency verified ({second_summary['skipped']} skipped).")

        current = service.retrieve(
            db,
            RetrievalRequest(
                tenant_id=tenant.id,
                query_text="shutdown complaints Component validation evidence",
                retrieval_mode="hybrid",
                top_k=5,
            ),
        )
        if current.results_count == 0:
            errors.append("Hybrid retrieval returned no evidence.")
            print("[FAIL] Hybrid retrieval returned no results.")
        else:
            print(f"[PASS] Hybrid retrieval returned {current.results_count} result(s).")

        if current.results and not all(result.source_anchor for result in current.results):
            errors.append("Retrieved material results missing source anchors.")
            print("[FAIL] Source-anchor coverage below 100%.")
        else:
            print("[PASS] Source-anchor coverage for retrieved material results: 100%.")

        product = db.query(Product).filter(Product.tenant_id == tenant.id, Product.product_identifier == "PRD-ASTER-100").first()
        version = None
        if product:
            version = (
                db.query(ProductVersion)
                .filter(ProductVersion.tenant_id == tenant.id, ProductVersion.product_id == product.id, ProductVersion.version_identifier == "D")
                .first()
            )
        if product and version:
            scoped = service.retrieve(
                db,
                RetrievalRequest(
                    tenant_id=tenant.id,
                    query_text="AsterFlow Rev D shutdown evidence",
                    retrieval_mode="hybrid",
                    product_id=product.id,
                    product_version_id=version.id,
                    top_k=10,
                ),
            )
            wrong_context = [
                result
                for result in scoped.results
                if not any(link["entity_type"] == "Product" and link["entity_id"] == str(product.id) for link in result.related_entities)
            ]
            if wrong_context:
                errors.append("Wrong Product evidence presented as applicable.")
                print("[FAIL] Product/ProductVersion context isolation failed.")
            else:
                print("[PASS] Product/ProductVersion context isolation verified.")
        else:
            print("[INFO] Product Rev D context not found; product isolation validation skipped.")

        as_of = dt.datetime(2026, 2, 15, tzinfo=dt.timezone.utc)
        event_view = service.retrieve(
            db,
            RetrievalRequest(
                tenant_id=tenant.id,
                query_text="late genealogy evidence Component shutdown",
                retrieval_mode="hybrid",
                temporal_mode="event",
                event_as_of=as_of,
                top_k=20,
            ),
        )
        known_view = service.retrieve(
            db,
            RetrievalRequest(
                tenant_id=tenant.id,
                query_text="late genealogy evidence Component shutdown",
                retrieval_mode="hybrid",
                temporal_mode="known",
                knowledge_as_of=as_of,
                top_k=20,
            ),
        )
        future_leaks = [
            result
            for result in known_view.results
            if result.temporal_context.get("ingestion_timestamp")
            and dt.datetime.fromisoformat(result.temporal_context["ingestion_timestamp"]) > as_of
        ]
        if future_leaks:
            errors.append("Future evidence leaked into KNOWN-AS-OF retrieval.")
            print("[FAIL] Future evidence leakage detected.")
        else:
            print("[PASS] Future evidence leakage in KNOWN-AS-OF: 0.")
        if {r.evidence_id for r in event_view.results} == {r.evidence_id for r in known_view.results}:
            print("[INFO] Event-as-of and known-as-of sets are identical for currently indexed corpus.")
        else:
            print("[PASS] Event-as-of and known-as-of returned distinct evidence sets.")

        no_match = service.retrieve(
            db,
            RetrievalRequest(
                tenant_id=tenant.id,
                query_text="unavailable comparative Rev A Rev B testing nonexistent",
                product_id=uuid.uuid4(),
                top_k=5,
            ),
        )
        if no_match.status != "NO_RELEVANT_EVIDENCE":
            errors.append("No-match behavior did not return NO_RELEVANT_EVIDENCE.")
            print("[FAIL] No-match behavior failed.")
        else:
            print("[PASS] No-match behavior returns NO_RELEVANT_EVIDENCE.")

        gt_indexed = db.execute(
            text(
                "SELECT count(*) FROM evidence_chunk_embeddings emb "
                "JOIN evidence e ON e.tenant_id=emb.tenant_id AND e.id=emb.evidence_id "
                "WHERE lower(e.evidence_identifier) LIKE '%ground_truth%'"
            )
        ).scalar()
        if gt_indexed:
            errors.append("Ground Truth evidence was indexed.")
            print("[FAIL] Ground Truth indexed.")
        else:
            print("[PASS] Ground Truth indexed: 0.")

        provenance_count = db.query(RetrievalQuery).filter(RetrievalQuery.tenant_id == tenant.id).count()
        if provenance_count == 0:
            errors.append("No retrieval provenance recorded.")
            print("[FAIL] Retrieval provenance missing.")
        else:
            print(f"[PASS] Retrieval provenance recorded ({provenance_count} query rows).")

        print("=" * 72)
        if errors:
            print(f"DAY 9 VALIDATION FAILED WITH {len(errors)} ERROR(S):")
            for error in errors:
                print(f"  - {error}")
            return 1

        print("DAY 9 VALIDATION PASSED — TRUSTED RETRIEVAL READY.")
        print("=" * 72)
        return 0
    except Exception as exc:
        print(f"[ERROR] Exception during Day 9 validation: {exc}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_day9_validation())
