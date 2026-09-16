import hashlib
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from backend.app.db.models.evidence_intelligence import EvidenceChunk
from backend.app.db.models.retrieval_intelligence import EvidenceChunkEmbedding


class EvidenceChunker:
    """Chunks evidence content into deterministic semantic blocks with source locators."""

    def __init__(self, target_chunk_size: int = 500, max_chunk_size: int = 1000):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size

    def create_chunks_for_evidence(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        evidence_id: uuid.UUID,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[EvidenceChunk]:
        """Splits content into EvidenceChunk records and persists them idempotently."""
        # Delete Day 9 embeddings first so Day 8 chunk reprocessing stays idempotent.
        existing_chunk_ids = [
            row.id
            for row in db.query(EvidenceChunk.id)
            .filter(
                EvidenceChunk.tenant_id == tenant_id,
                EvidenceChunk.evidence_id == evidence_id,
            )
            .all()
        ]
        if existing_chunk_ids:
            db.query(EvidenceChunkEmbedding).filter(
                EvidenceChunkEmbedding.tenant_id == tenant_id,
                EvidenceChunkEmbedding.chunk_id.in_(existing_chunk_ids),
            ).delete(synchronize_session=False)

        db.query(EvidenceChunk).filter(
            EvidenceChunk.tenant_id == tenant_id,
            EvidenceChunk.evidence_id == evidence_id,
        ).delete(synchronize_session=False)

        raw_chunks = self._chunk_text(content)
        chunk_objects: List[EvidenceChunk] = []

        for seq, (chunk_text, anchor) in enumerate(raw_chunks, start=1):
            chksum = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            token_est = len(chunk_text.split())

            chunk_obj = EvidenceChunk(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                sequence_number=seq,
                text_content=chunk_text,
                source_anchor=anchor,
                token_count=token_est,
                checksum=chksum,
            )
            db.add(chunk_obj)
            chunk_objects.append(chunk_obj)

        db.flush()
        return chunk_objects

    def _chunk_text(self, content: str) -> List[tuple[str, Dict[str, Any]]]:
        """Deterministically breaks content into paragraph or section blocks."""
        chunks: List[tuple[str, Dict[str, Any]]] = []

        if not content or not content.strip():
            return [("", {"section": "empty", "character_range": [0, 0]})]

        # Break by double newline or CSV/JSON boundaries
        lines = content.splitlines()
        current_block: List[str] = []
        current_len = 0
        start_char = 0
        p_index = 0

        for line in lines:
            line_str = line.strip()
            if not line_str:
                if current_block:
                    block_text = "\n".join(current_block)
                    end_char = start_char + len(block_text)
                    anchor = {
                        "paragraph_index": p_index,
                        "character_range": [start_char, end_char],
                        "excerpt": block_text[:100],
                    }
                    chunks.append((block_text, anchor))
                    p_index += 1
                    start_char = end_char + 1
                    current_block = []
                    current_len = 0
                continue

            current_block.append(line)
            current_len += len(line)

            if current_len >= self.target_chunk_size:
                block_text = "\n".join(current_block)
                end_char = start_char + len(block_text)
                anchor = {
                    "paragraph_index": p_index,
                    "character_range": [start_char, end_char],
                    "excerpt": block_text[:100],
                }
                chunks.append((block_text, anchor))
                p_index += 1
                start_char = end_char + 1
                current_block = []
                current_len = 0

        if current_block:
            block_text = "\n".join(current_block)
            end_char = start_char + len(block_text)
            anchor = {
                "paragraph_index": p_index,
                "character_range": [start_char, end_char],
                "excerpt": block_text[:100],
            }
            chunks.append((block_text, anchor))

        return chunks
