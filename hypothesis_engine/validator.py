from hypothesis_engine.schemas import Hypothesis, HypothesisEvidenceRelationship


FORBIDDEN_STATUS = {"PROVEN", "ROOT_CAUSE", "ESTABLISHED_ROOT_CAUSE"}
FORBIDDEN_NUMERIC_TERMS = ["% probability", "confidence score", "root-cause likelihood"]
CAUSAL_FACT_PHRASES = ["is the root cause", "proven root cause", "established cause", "caused all"]


class HypothesisValidator:
    def validate(self, hypotheses: list[Hypothesis]) -> tuple[list[Hypothesis], list[Hypothesis], dict[str, int | float]]:
        accepted: list[Hypothesis] = []
        rejected: list[Hypothesis] = []
        relationships = 0
        grounded = 0
        evidence_derived = 0
        anchored = 0
        unsupported_relationships = 0
        unsupported_causal = 0
        forced_probabilities = 0

        for hypothesis in hypotheses:
            invalid = False
            text = hypothesis.statement.lower()
            if hypothesis.status in FORBIDDEN_STATUS:
                invalid = True
            if any(phrase in text for phrase in CAUSAL_FACT_PHRASES):
                unsupported_causal += 1
                invalid = True
            if any(term in text for term in FORBIDDEN_NUMERIC_TERMS):
                forced_probabilities += 1
                invalid = True

            for relation in self._relations(hypothesis):
                relationships += 1
                if relation.source_references:
                    grounded += 1
                else:
                    unsupported_relationships += 1
                    invalid = True
                if any(ref.reference_type in {"EVIDENCE", "OBSERVATION", "RETRIEVAL_RESULT"} for ref in relation.source_references):
                    evidence_derived += 1
                    if any(ref.source_anchor for ref in relation.source_references if ref.reference_type in {"EVIDENCE", "OBSERVATION", "RETRIEVAL_RESULT"}):
                        anchored += 1

            if invalid:
                rejected.append(hypothesis)
            else:
                accepted.append(hypothesis)

        material_grounding = 1.0 if relationships == 0 else grounded / relationships
        source_anchor_coverage = 1.0 if evidence_derived == 0 else anchored / evidence_derived
        return accepted, rejected, {
            "hypotheses_total": len(hypotheses),
            "hypotheses_accepted": len(accepted),
            "hypotheses_rejected": len(rejected),
            "material_evidence_relationships": relationships,
            "grounded_evidence_relationships": grounded,
            "evidence_derived_relationships": evidence_derived,
            "anchored_evidence_relationships": anchored,
            "material_grounding_coverage": material_grounding,
            "source_anchor_coverage": source_anchor_coverage,
            "unsupported_material_evidence_relationships": unsupported_relationships,
            "invented_evidence": unsupported_relationships,
            "unsupported_causal_conclusions": unsupported_causal,
            "forced_numeric_probabilities": forced_probabilities,
        }

    def _relations(self, hypothesis: Hypothesis) -> list[HypothesisEvidenceRelationship]:
        return hypothesis.supporting_evidence + hypothesis.contradicting_evidence + hypothesis.contextual_evidence
