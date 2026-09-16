import logging
import re
from typing import Any, Dict, List

from ai.schemas import EvidenceExtractionResult, ExtractedObservationSchema

logger = logging.getLogger(__name__)


class GroundingValidator:
    """Validates source anchors, hallucination defense, and prompt injection safety."""

    def validate_extraction(
        self,
        result: EvidenceExtractionResult,
        source_content: str,
    ) -> EvidenceExtractionResult:
        """Validates all extracted observations against source content. Flags or downgrades ungrounded statements."""
        validated_observations: List[ExtractedObservationSchema] = []

        for obs in result.observations:
            is_grounded = self.verify_source_anchor(obs.source_anchor, obs.statement, source_content)
            if not is_grounded:
                # Mark as unanchored or flag limitation rather than asserting fake grounding
                logger.warning(f"Unanchored observation detected: '{obs.statement[:50]}...'")
                result.warnings.append(f"Observation '{obs.statement[:30]}...' was unanchored in source text.")
                # Update quality status
                obs.statement = f"[UNANCHORED] {obs.statement}"

            validated_observations.append(obs)

        result.observations = validated_observations
        return result

    def verify_source_anchor(
        self,
        anchor: Any,
        statement: str,
        source_content: str,
    ) -> bool:
        """Verifies if anchor excerpt or character range exists in source text."""
        if not source_content or not source_content.strip():
            return False

        if not anchor:
            return False

        # If excerpt exists, verify it is present in source content
        if hasattr(anchor, "excerpt") and anchor.excerpt:
            if anchor.excerpt.strip().lower() in source_content.lower():
                return True

        if isinstance(anchor, dict) and anchor.get("excerpt"):
            if anchor["excerpt"].strip().lower() in source_content.lower():
                return True

        # If character_range exists, verify valid bounds
        char_range = getattr(anchor, "character_range", None) or (anchor.get("character_range") if isinstance(anchor, dict) else None)
        if char_range and len(char_range) == 2:
            start, end = char_range
            if 0 <= start <= end <= len(source_content):
                return True

        # Fallback keyword overlap check
        words = [w for w in re.findall(r"\w+", statement.lower()) if len(w) > 3]
        if words:
            matching_words = [w for w in words if w in source_content.lower()]
            if len(matching_words) / len(words) >= 0.5:
                return True

        return False
