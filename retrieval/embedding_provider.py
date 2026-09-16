import hashlib
import math
import re
from dataclasses import dataclass

from backend.app.db.models.retrieval_intelligence import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_PIPELINE_VERSION,
    EMBEDDING_PROVIDER,
)


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


@dataclass(frozen=True)
class EmbeddingMetadata:
    provider: str
    model: str
    model_version: str
    dimension: int
    pipeline_version: str
    distance_metric: str = "cosine"


class DeterministicEmbeddingProvider:
    """Local deterministic embedding provider for controlled R1 retrieval tests."""

    def model_metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata(
            provider=EMBEDDING_PROVIDER,
            model=EMBEDDING_MODEL,
            model_version=EMBEDDING_MODEL_VERSION,
            dimension=EMBEDDING_DIMENSION,
            pipeline_version=EMBEDDING_PIPELINE_VERSION,
        )

    def embed_text(self, text: str) -> list[float]:
        if "EMBEDDING_FAIL" in text:
            raise ValueError("Controlled embedding failure marker encountered.")

        vector = [0.0] * EMBEDDING_DIMENSION
        tokens = TOKEN_PATTERN.findall((text or "").lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSION
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 16) / 16.0
            vector[index] += sign * weight

        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude == 0:
            return vector
        return [round(v / magnitude, 8) for v in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
