import json
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from backend.app.db.models.evidence_intelligence import EvidenceObservation


class DeterministicExtractor:
    """Extracts known structured entities, dates, test results, and metadata without LLM calls."""

    def extract_deterministic_observations(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        evidence_id: uuid.UUID,
        content: str,
        metadata: Dict[str, Any],
    ) -> List[EvidenceObservation]:
        """Extracts deterministic observations from metadata and content."""
        observations: List[EvidenceObservation] = []

        # 1. Title/Metadata explicit statement
        if metadata.get("title"):
            obs = EvidenceObservation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                statement=f"Evidence metadata: {metadata['title']} ({metadata.get('evidence_type')})",
                observation_type="EXPLICIT_SOURCE_STATEMENT",
                extraction_method="DETERMINISTIC",
                source_anchor={"source": "metadata", "field": "title"},
                quality_status="VALIDATED",
            )
            db.add(obs)
            observations.append(obs)

        # 2. Extract explicit test results (e.g., PASS / FAIL)
        test_matches = re.finditer(r"(validation|test|result|status)[:\s]+(PASS|FAILED|PASSED|FAIL|COMPLETED)", content, re.IGNORECASE)
        for m in test_matches:
            obs = EvidenceObservation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                statement=f"Test result stated: {m.group(0)}",
                observation_type="STRUCTURED_EXTRACTION",
                extraction_method="DETERMINISTIC",
                source_anchor={
                    "excerpt": m.group(0),
                    "character_range": [m.start(), m.end()],
                },
                quality_status="VALIDATED",
            )
            db.add(obs)
            observations.append(obs)

        # 3. Extract explicit dates
        date_matches = re.finditer(r"\b(20\d{2}-\d{2}-\d{2}|\d{2}/[A-Za-z]{3}/20\d{2}|\d{2}-\d{2}-20\d{2})\b", content)
        for m in date_matches:
            obs = EvidenceObservation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                statement=f"Explicit date in evidence: {m.group(0)}",
                observation_type="STRUCTURED_EXTRACTION",
                extraction_method="DETERMINISTIC",
                source_anchor={
                    "excerpt": m.group(0),
                    "character_range": [m.start(), m.end()],
                },
                quality_status="VALIDATED",
            )
            db.add(obs)
            observations.append(obs)

        db.flush()
        return observations
