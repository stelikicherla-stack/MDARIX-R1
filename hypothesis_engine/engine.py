import uuid
from datetime import datetime, timezone

from investigator.schemas import AnalysisItem, InvestigationAnalysis, SourceReference
from hypothesis_engine.schemas import Hypothesis, HypothesisEvidenceRelationship, HypothesisSet


PROVIDER = "mdarix-controlled-hypothesis-engine"
MODEL = "mdarix-rule-grounded-hypothesis-engine"
MODEL_VERSION = "1.0"
ORCHESTRATION_VERSION = "R1-Day12"
PROMPT_TEMPLATE_VERSION = "R1-Day12-Hypothesis-v1"


class ControlledHypothesisEngine:
    def generate(self, analysis: InvestigationAnalysis, investigator_question: str | None = None) -> HypothesisSet:
        now = datetime.now(timezone.utc)
        source_refs = analysis.source_references or [ref for item in analysis.accepted_items() for ref in item.source_references][:8]
        possible = analysis.possible_explanations
        hypotheses: list[Hypothesis] = []

        if not possible or analysis.status == "FAILED_VALIDATION":
            hypotheses.append(self._no_viable_hypothesis(analysis, source_refs, now))
        else:
            hypotheses.extend(self._candidate_hypotheses(analysis, source_refs, now, investigator_question))

        return HypothesisSet(
            hypothesis_set_id=uuid.uuid4(),
            investigation_id=analysis.investigation_id,
            source_analysis_id=analysis.analysis_id,
            source_ai_execution_id=analysis.ai_execution_id,
            context_snapshot_id=analysis.context_snapshot_id,
            context_snapshot_version=analysis.context_snapshot_version,
            status="INSUFFICIENT_EVIDENCE" if len(hypotheses) == 1 and hypotheses[0].status == "NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS" else "MIXED_EVIDENCE",
            hypotheses=hypotheses,
            comparison=[self._comparison_row(item) for item in hypotheses],
            validation_summary={},
            guardrails={
                "hypothesis_is_not_fact": True,
                "hypothesis_is_not_root_cause": True,
                "support_is_not_proof": True,
                "no_forced_numeric_probability": True,
                "human_authority_required": True,
                "retrieval_rank_is_not_truth": True,
                "graph_path_is_not_causality": True,
            },
            provenance={
                "provider": PROVIDER,
                "model": MODEL,
                "model_version": MODEL_VERSION,
                "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                "orchestration_version": ORCHESTRATION_VERSION,
                "source_analysis_id": str(analysis.analysis_id),
                "hidden_chain_of_thought_persisted": False,
            },
            created_at=now,
        )

    def _candidate_hypotheses(self, analysis: InvestigationAnalysis, refs: list[SourceReference], now: datetime, investigator_question: str | None) -> list[Hypothesis]:
        hypotheses: list[Hypothesis] = []
        text = " ".join(item.statement for item in analysis.possible_explanations + analysis.questions_to_investigate + analysis.limitations).lower()
        explanations = analysis.possible_explanations

        if any(term in text for term in ["supplier", "component", "rev b", "comp-pwr", "process"]):
            hypotheses.append(
                self._hypothesis(
                    analysis,
                    "Component or supplier-process change contributed to the observed shutdown increase.",
                    "component_supplier_change",
                    refs,
                    now,
                    supporting=[item for item in explanations if any(term in item.statement.lower() for term in ["supplier", "component"])],
                    alternatives=[
                        "Manufacturing or lot variation may explain part of the pattern.",
                        "Configuration or use factors may contribute independently of the component change.",
                    ],
                )
            )
        if any(term in text for term in ["manufacturing", "lot", "traceability"]):
            hypotheses.append(
                self._hypothesis(
                    analysis,
                    "Manufacturing or lot variation contributed to the shutdown pattern independently or jointly.",
                    "manufacturing_lot_variation",
                    refs,
                    now,
                    supporting=[item for item in explanations if any(term in item.statement.lower() for term in ["manufacturing", "lot"])],
                    alternatives=[
                        "Component susceptibility may still be relevant.",
                        "The observed increase may reflect multiple concurrent factors.",
                    ],
                )
            )
        hypotheses.append(
            self._hypothesis(
                analysis,
                "Multiple factors jointly contributed to the observed increase, with current evidence insufficient to isolate one cause.",
                "multi_factor_explanation",
                refs,
                now,
                supporting=explanations[:3],
                alternatives=[
                    "A single component/supplier factor may explain a subset of cases.",
                    "A manufacturing/lot factor may explain a subset of cases.",
                ],
            )
        )

        if investigator_question and self._leading(investigator_question):
            for hypothesis in hypotheses:
                hypothesis.assumptions.append("The user's premise is treated as a question to test, not as established fact.")
        return hypotheses

    def _hypothesis(
        self,
        analysis: InvestigationAnalysis,
        statement: str,
        scope: str,
        refs: list[SourceReference],
        now: datetime,
        supporting: list[AnalysisItem],
        alternatives: list[str],
    ) -> Hypothesis:
        support_refs = [ref for item in supporting for ref in item.source_references] or refs[:3]
        contradiction_refs = [ref for item in analysis.contradictions for ref in item.source_references] or refs[:2]
        limitation_refs = [ref for item in analysis.missing_information + analysis.limitations for ref in item.source_references] or refs[:2]
        status = "MIXED_EVIDENCE" if analysis.contradictions or analysis.missing_information else "UNDER_INVESTIGATION"
        return Hypothesis(
            hypothesis_id=uuid.uuid4(),
            investigation_id=analysis.investigation_id,
            statement=statement,
            scope=scope,
            status=status,
            related_objects=self._related_objects(support_refs + contradiction_refs),
            supporting_evidence=[
                self._relationship("SUPPORTS", "Available analysis contains observations or possible explanations consistent with this hypothesis.", support_refs[:4], analysis)
            ],
            contradicting_evidence=[
                self._relationship("CONTRADICTS", "Contradictory or tension-bearing evidence must be resolved before this hypothesis can be narrowed.", contradiction_refs[:4], analysis)
            ],
            contextual_evidence=[
                self._relationship("CONTEXTUAL", "Workspace and temporal context frame this hypothesis but do not prove it.", limitation_refs[:4], analysis)
            ],
            unknowns=[item.statement for item in analysis.missing_information[:4]],
            assumptions=[
                "Complaint coding is sufficiently consistent across compared periods.",
                "Configuration and genealogy mappings are materially complete where used.",
                "Temporal ordering in source systems reflects actual field and knowledge timing.",
            ],
            temporal_consistency=self._temporal_consistency(analysis),
            evidence_gaps=[item.statement for item in (analysis.missing_information + analysis.limitations)[:5]],
            falsification_conditions=self._falsification_conditions(scope),
            alternative_explanations=alternatives,
            source_references=(support_refs + contradiction_refs + limitation_refs)[:8],
            context_snapshot={
                "context_snapshot_id": analysis.context_snapshot_id,
                "context_snapshot_version": analysis.context_snapshot_version,
                "source_analysis_id": str(analysis.analysis_id),
            },
            provenance={
                "source_analysis_id": str(analysis.analysis_id),
                "source_ai_execution_id": str(analysis.ai_execution_id) if analysis.ai_execution_id else None,
                "hypothesis_semantics": "hypothesis_to_test_not_fact_or_root_cause",
            },
            created_at=now,
            updated_at=now,
        )

    def _no_viable_hypothesis(self, analysis: InvestigationAnalysis, refs: list[SourceReference], now: datetime) -> Hypothesis:
        return Hypothesis(
            hypothesis_id=uuid.uuid4(),
            investigation_id=analysis.investigation_id,
            statement="No currently supportable hypothesis can be generated from the available grounded analysis.",
            scope="insufficient_evidence",
            status="NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS",
            supporting_evidence=[],
            contradicting_evidence=[],
            contextual_evidence=[
                self._relationship("INSUFFICIENT", "Available analysis abstained or lacks enough grounded possible explanations.", refs[:3], analysis)
            ],
            unknowns=[item.statement for item in analysis.missing_information[:4]],
            assumptions=[],
            temporal_consistency={"status": "INSUFFICIENT_TEMPORAL_EVIDENCE", "rationale": "No viable hypothesis to check temporally."},
            evidence_gaps=[item.statement for item in analysis.limitations[:4]],
            falsification_conditions=["Additional grounded evidence would be required before testing a hypothesis."],
            alternative_explanations=[],
            source_references=refs[:5],
            context_snapshot={"context_snapshot_id": analysis.context_snapshot_id, "context_snapshot_version": analysis.context_snapshot_version},
            provenance={"source_analysis_id": str(analysis.analysis_id)},
            created_at=now,
            updated_at=now,
        )

    def _relationship(self, rel_type: str, rationale: str, refs: list[SourceReference], analysis: InvestigationAnalysis) -> HypothesisEvidenceRelationship:
        return HypothesisEvidenceRelationship(
            relationship_id=f"HER-{uuid.uuid4().hex[:12]}",
            relationship_type=rel_type,
            rationale=rationale,
            source_references=refs,
            provenance={"source_analysis_id": str(analysis.analysis_id), "relationship_semantics": "evidence_relationship_not_probability"},
        )

    def _temporal_consistency(self, analysis: InvestigationAnalysis) -> dict:
        payload = analysis.model_dump_json().lower()
        if "pre-rev" in payload or "before" in payload:
            return {
                "status": "PARTIALLY_CONSISTENT",
                "rationale": "Chronology may support later contribution but does not support all-event causality.",
            }
        if analysis.temporal_context.get("mode") == "known":
            return {
                "status": "CONSISTENT",
                "rationale": "Hypothesis set generated from known-as-of constrained context.",
            }
        return {
            "status": "PARTIALLY_CONSISTENT",
            "rationale": "Temporal context is present but causal timing remains unproven.",
        }

    def _falsification_conditions(self, scope: str) -> list[str]:
        common = [
            "Equivalent shutdown rates across affected and unaffected configurations would weaken this hypothesis.",
            "Affected units definitively lacking the implicated object would weaken this hypothesis.",
            "Independent evidence explaining affected lots or use conditions would weaken this hypothesis.",
        ]
        if scope == "component_supplier_change":
            return common + ["Comparative Rev A / Rev B testing showing no relevant behavioral difference would weaken this hypothesis."]
        if scope == "manufacturing_lot_variation":
            return common + ["Complete lot genealogy showing no lot/process clustering would weaken this hypothesis."]
        return common + ["Evidence isolating one sufficient explanation would weaken a multi-factor explanation."]

    def _related_objects(self, refs: list[SourceReference]) -> list[dict]:
        objects = []
        for ref in refs:
            if ref.evidence_identifier:
                objects.append({"object_type": "Evidence", "identifier": ref.evidence_identifier})
        seen = set()
        unique = []
        for item in objects:
            key = (item["object_type"], item["identifier"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique[:10]

    def _comparison_row(self, hypothesis: Hypothesis) -> dict:
        return {
            "hypothesis_id": str(hypothesis.hypothesis_id),
            "scope": hypothesis.scope,
            "status": hypothesis.status,
            "support_count": len(hypothesis.supporting_evidence),
            "contradiction_count": len(hypothesis.contradicting_evidence),
            "gap_count": len(hypothesis.evidence_gaps),
            "temporal_fit": hypothesis.temporal_consistency.get("status"),
            "no_winner_score": True,
        }

    def _leading(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in ["obviously", "show me why", "prove", "confirm", "root cause"])
