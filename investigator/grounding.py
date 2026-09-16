from investigator.schemas import AnalysisItem, GroundingStatus


FACTUAL_TYPES = {
    "OBSERVATION",
    "DETERMINISTIC_RELATIONSHIP",
    "SOURCE_ATTRIBUTED_CONCLUSION",
    "TEMPORAL_PATTERN",
}
INTERPRETIVE_TYPES = {
    "POSSIBLE_EXPLANATION",
    "CONTRADICTION",
    "MISSING_INFORMATION",
    "INVESTIGATIVE_QUESTION",
    "LIMITATION",
    "ASSUMPTION",
    "INSUFFICIENT_EVIDENCE",
}


class GroundingValidator:
    def validate_items(self, items: list[AnalysisItem]) -> tuple[list[AnalysisItem], list[AnalysisItem], dict[str, int]]:
        accepted: list[AnalysisItem] = []
        rejected: list[AnalysisItem] = []
        evidence_derived = 0
        anchored = 0

        for item in items:
            status = self.validate_item(item)
            checked = item.model_copy(update={"grounding_status": status})
            if self._requires_evidence_anchor(checked):
                evidence_derived += 1
                if any(ref.source_anchor for ref in checked.source_references):
                    anchored += 1
            if status == "ACCEPTED":
                accepted.append(checked)
            else:
                rejected.append(checked)

        return accepted, rejected, {
            "material_items": len(items),
            "accepted_items": len(accepted),
            "rejected_items": len(rejected),
            "evidence_derived_items": evidence_derived,
            "evidence_derived_items_with_source_anchor": anchored,
        }

    def validate_item(self, item: AnalysisItem) -> GroundingStatus:
        if item.semantic_type in FACTUAL_TYPES and not item.source_references:
            return "REJECTED_UNGROUNDED"
        if self._requires_evidence_anchor(item) and not any(ref.source_anchor for ref in item.source_references):
            return "REJECTED_UNGROUNDED"
        if item.semantic_type in INTERPRETIVE_TYPES and not (item.source_references or item.limitations):
            return "INSUFFICIENT_EVIDENCE"
        return "ACCEPTED"

    def _requires_evidence_anchor(self, item: AnalysisItem) -> bool:
        return any(ref.reference_type in {"EVIDENCE", "OBSERVATION", "RETRIEVAL_RESULT"} for ref in item.source_references)
