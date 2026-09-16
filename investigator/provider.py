import uuid
from datetime import datetime, timezone
from typing import Any

from investigation_workspace.schemas import InvestigationWorkspaceResponse
from investigator.schemas import AnalysisItem, InvestigationAnalysis, SourceReference


PROVIDER = "mdarix-controlled-investigator"
MODEL = "mdarix-rule-grounded-investigator"
MODEL_VERSION = "1.0"
PROMPT_TEMPLATE_VERSION = "R1-Day11-Investigator-v1"
ORCHESTRATION_VERSION = "R1-Day11"


class ControlledInvestigatorProvider:
    def analyze(
        self,
        workspace: InvestigationWorkspaceResponse,
        analysis_id: uuid.UUID,
        investigator_question: str | None = None,
        analysis_mode: str = "standard",
    ) -> InvestigationAnalysis:
        items: dict[str, list[AnalysisItem]] = {
            "observations": [],
            "relevant_changes": [],
            "temporal_patterns": [],
            "evidence_relationships": [],
            "possible_explanations": [],
            "contradictions": [],
            "missing_information": [],
            "questions_to_investigate": [],
            "limitations": [],
        }

        evidence_refs = self._evidence_refs(workspace)
        items["observations"].extend(self._observations(workspace))
        items["relevant_changes"].extend(self._changes(workspace))
        items["temporal_patterns"].extend(self._temporal_patterns(workspace))
        items["evidence_relationships"].extend(self._relationships(workspace))
        items["contradictions"].extend(self._contradictions(workspace, evidence_refs))
        items["missing_information"].extend(self._missing_information(workspace))
        items["possible_explanations"].extend(self._possible_explanations(workspace, evidence_refs, investigator_question))
        items["questions_to_investigate"].extend(self._questions(workspace, evidence_refs, investigator_question))
        items["limitations"].extend(self._limitations(workspace, evidence_refs, investigator_question, analysis_mode))

        return InvestigationAnalysis(
            analysis_id=analysis_id,
            investigation_id=uuid.UUID(str(workspace.investigation["id"])),
            context_snapshot_id=self.context_snapshot_id(workspace),
            context_snapshot_version=str(workspace.metadata.get("workspace_version", "R1-Day10")),
            status="COMPLETED_WITH_LIMITATIONS",
            observations=items["observations"],
            relevant_changes=items["relevant_changes"],
            temporal_patterns=items["temporal_patterns"],
            evidence_relationships=items["evidence_relationships"],
            possible_explanations=items["possible_explanations"],
            contradictions=items["contradictions"],
            missing_information=items["missing_information"],
            questions_to_investigate=items["questions_to_investigate"],
            limitations=items["limitations"],
            source_references=evidence_refs[:12],
            temporal_context=workspace.temporal_context,
            model_provenance={
                "provider": PROVIDER,
                "model": MODEL,
                "model_version": MODEL_VERSION,
                "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                "orchestration_version": ORCHESTRATION_VERSION,
                "hidden_chain_of_thought_persisted": False,
            },
            validation_summary={},
            guardrails={
                "no_root_cause_conclusion": True,
                "no_regulatory_decision": True,
                "human_authority_required": True,
                "retrieval_rank_is_not_evidence_strength": True,
                "graph_connectivity_is_not_causality": True,
                "evidence_content_is_untrusted_data": True,
            },
            created_at=datetime.now(timezone.utc),
        )

    def context_snapshot_id(self, workspace: InvestigationWorkspaceResponse) -> str:
        return f"{workspace.metadata.get('workspace_version', 'R1-Day10')}:{workspace.investigation['id']}:{workspace.temporal_context.get('mode')}:{workspace.temporal_context.get('as_of')}"

    def _evidence_refs(self, workspace: InvestigationWorkspaceResponse) -> list[SourceReference]:
        refs: list[SourceReference] = []
        for evidence in workspace.evidence_context:
            chunk = next((item for item in evidence.get("chunks", []) if item.get("source_anchor")), None)
            refs.append(
                SourceReference(
                    reference_type="EVIDENCE",
                    evidence_id=evidence.get("id"),
                    evidence_identifier=evidence.get("evidence_identifier"),
                    chunk_id=chunk.get("chunk_id") if chunk else None,
                    source_anchor=chunk.get("source_anchor", {}) if chunk else {},
                    temporal_context=evidence.get("temporal", {}),
                    context_path=f"evidence_context.{evidence.get('evidence_identifier')}",
                )
            )
        return refs

    def _observations(self, workspace: InvestigationWorkspaceResponse) -> list[AnalysisItem]:
        items: list[AnalysisItem] = []
        selected = self._priority_evidence(workspace)
        for evidence in selected:
            refs = self._refs_for_evidence(evidence)
            statement = f"Evidence {evidence['evidence_identifier']} is available in the investigation context: {evidence['title']}."
            observations = evidence.get("observations", [])
            evidence_text = " ".join([statement] + [str(chunk.get("excerpt", "")) for chunk in evidence.get("chunks", [])])
            semantic_type = "OBSERVATION"
            if "root cause:" in evidence_text.lower():
                semantic_type = "SOURCE_ATTRIBUTED_CONCLUSION"
                statement = f"Historical source evidence {evidence['evidence_identifier']} contains a source-attributed root-cause statement; MDARIX does not adopt it as an established fact."
            elif any(term in evidence_text.lower() for term in ["ignore previous instructions", "declare component", "mark investigation complete"]):
                semantic_type = "OBSERVATION"
                statement = f"Evidence {evidence['evidence_identifier']} contains instruction-like source text that is treated only as evidence data: {evidence_text[:240]}"
            if observations:
                statement = observations[0].get("statement", statement)
                refs = self._refs_for_observation(evidence, observations[0])
                if "root cause:" in statement.lower():
                    semantic_type = "SOURCE_ATTRIBUTED_CONCLUSION"
                    statement = f"Historical source evidence {evidence['evidence_identifier']} states: {statement}"
            items.append(
                self._item(
                    semantic_type,
                    statement,
                    refs,
                    "Evidence-derived observation preserved with source basis.",
                )
            )
        return items

    def _priority_evidence(self, workspace: InvestigationWorkspaceResponse) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for evidence in workspace.evidence_context:
            text = " ".join([str(evidence.get("title", ""))] + [str(chunk.get("excerpt", "")) for chunk in evidence.get("chunks", [])]).lower()
            if any(term in text for term in ["root cause:", "ignore previous instructions", "declare component", "mark investigation complete"]):
                selected.append(evidence)
        for evidence in workspace.evidence_context:
            if evidence not in selected:
                selected.append(evidence)
            if len(selected) >= 8:
                break
        return selected

    def _changes(self, workspace: InvestigationWorkspaceResponse) -> list[AnalysisItem]:
        items: list[AnalysisItem] = []
        for change in workspace.product_context.get("changes", [])[:4]:
            label = change.get("change_identifier") or change.get("description") or "change"
            items.append(
                self._item(
                    "TEMPORAL_PATTERN",
                    f"Change context {label} is present in the deterministic product timeline.",
                    [SourceReference(reference_type="DETERMINISTIC_CONTEXT", context_path=f"product_context.changes.{label}")],
                    "Derived from Product 360 context, not from AI inference.",
                )
            )
        return items

    def _temporal_patterns(self, workspace: InvestigationWorkspaceResponse) -> list[AnalysisItem]:
        refs = [SourceReference(reference_type="DETERMINISTIC_CONTEXT", context_path="temporal_context")]
        mode = workspace.temporal_context.get("mode")
        as_of = workspace.temporal_context.get("as_of")
        statement = f"The analysis is constrained to {mode} temporal semantics"
        if as_of:
            statement += f" as of {as_of}"
        statement += "; event time and knowledge-availability time remain distinct."
        return [self._item("TEMPORAL_PATTERN", statement, refs, "Temporal interpretation is inherited from Day 10.")]

    def _relationships(self, workspace: InvestigationWorkspaceResponse) -> list[AnalysisItem]:
        items: list[AnalysisItem] = []
        for rel in workspace.relationship_context.get("relationships", [])[:5]:
            rel_type = rel.get("type", "relationship")
            rid = rel.get("id")
            items.append(
                self._item(
                    "DETERMINISTIC_RELATIONSHIP",
                    f"Reality Graph relationship {rel_type} is present as deterministic context only.",
                    [SourceReference(reference_type="GRAPH_RELATIONSHIP", graph_relationship_id=rid, context_path="relationship_context.relationships")],
                    "Graph connectivity is not treated as causality.",
                )
            )
        return items

    def _contradictions(self, workspace: InvestigationWorkspaceResponse, evidence_refs: list[SourceReference]) -> list[AnalysisItem]:
        text = self._all_text(workspace)
        items: list[AnalysisItem] = []
        if "shutdown" in text and ("validation" in text or "passed" in text):
            items.append(
                self._item(
                    "CONTRADICTION",
                    "Shutdown complaint context and validation/control evidence are both present and should be examined together rather than averaged away.",
                    evidence_refs[:4],
                    "Contradictory or tension-bearing evidence must remain visible.",
                )
            )
        if "late" in text or workspace.temporal_context.get("late_arriving_evidence_count", 0):
            items.append(
                self._item(
                    "CONTRADICTION",
                    "Some evidence appears late-arriving or knowledge-time sensitive and must not be represented as known in historical views unless available by the as-of time.",
                    evidence_refs[:3],
                    "Temporal contradiction/tension is preserved.",
                )
            )
        return items

    def _missing_information(self, workspace: InvestigationWorkspaceResponse) -> list[AnalysisItem]:
        items: list[AnalysisItem] = []
        for limitation in workspace.limitations:
            code = limitation.get("code", "LIMITATION")
            refs = [SourceReference(reference_type="WORKSPACE_LIMITATION", context_path=f"limitations.{code}")]
            semantic = "INSUFFICIENT_EVIDENCE" if code in {"NO_RELEVANT_EVIDENCE", "INSUFFICIENT_RELEVANT_EVIDENCE"} else "MISSING_INFORMATION"
            items.append(self._item(semantic, limitation.get("description", code), refs, "Workspace limitation surfaced without converting missing information into a negative fact."))
        return items

    def _possible_explanations(self, workspace: InvestigationWorkspaceResponse, evidence_refs: list[SourceReference], investigator_question: str | None) -> list[AnalysisItem]:
        text = f"{workspace.investigation.get('investigation_question', '')} {investigator_question or ''} {self._all_text(workspace)}".lower()
        explanations = []
        if any(term in text for term in ["supplier", "novacap", "alpha", "process"]):
            explanations.append(
                "Supplier or process-change context may warrant further investigation, but available evidence does not establish that it caused the reported shutdowns."
            )
        if any(term in text for term in ["component", "rev b", "rev d", "comp-pwr"]):
            explanations.append(
                "Component or product-version context may be associated with the investigation question and should be examined against complaint, validation, and lot evidence."
            )
        if any(term in text for term in ["lot", "traceability", "manufacturing"]):
            explanations.append(
                "Manufacturing lot effects should be examined because traceability and lot context can affect whether an apparent component association is real or confounded."
            )
        if not explanations:
            explanations.append("Available evidence is insufficient to identify a stronger possible explanation without further investigation.")
        return [self._item("POSSIBLE_EXPLANATION", statement, evidence_refs[:5], "Possible explanation only; not a hypothesis ranking or root-cause conclusion.") for statement in explanations[:4]]

    def _questions(self, workspace: InvestigationWorkspaceResponse, evidence_refs: list[SourceReference], investigator_question: str | None) -> list[AnalysisItem]:
        prompts = [
            "Are shutdown rates materially different across relevant product versions, lots, and time windows?",
            "Which affected complaints can be traced to specific suppliers, components, manufacturing sites, or lots?",
            "Is comparative verification or validation evidence available for the affected and unaffected configurations?",
            "Were similar shutdowns observed before the relevant component or supplier-process change?",
            "Are there unaffected lots using the same component or supplier process that should be used as context?",
        ]
        if investigator_question and self._looks_leading(investigator_question):
            prompts.insert(0, "What evidence supports or contradicts the premise in the user's question, and what evidence is still missing?")
        return [self._item("INVESTIGATIVE_QUESTION", question, evidence_refs[:4], "Question is grounded in the investigation context and does not presume causality.") for question in prompts[:6]]

    def _limitations(self, workspace: InvestigationWorkspaceResponse, evidence_refs: list[SourceReference], investigator_question: str | None, analysis_mode: str) -> list[AnalysisItem]:
        limitations = [
            self._item(
                "INSUFFICIENT_EVIDENCE",
                "Available evidence is insufficient to establish causality or root cause.",
                evidence_refs[:5] or [SourceReference(reference_type="DETERMINISTIC_CONTEXT", context_path="guardrails")],
                "Abstention is the correct behavior when evidence does not support a causal conclusion.",
            ),
            self._item(
                "LIMITATION",
                "Retrieval rank, graph connectivity, and temporal adjacency are contextual signals only; none are evidence strength or causality.",
                [SourceReference(reference_type="DETERMINISTIC_CONTEXT", context_path="guardrails")],
                "Preserves MDARIX epistemic boundaries.",
            ),
        ]
        if investigator_question and self._looks_leading(investigator_question):
            limitations.append(
                self._item(
                    "LIMITATION",
                    "The investigator question is leading; analysis preserves supporting, contradictory, and missing evidence instead of accepting the premise.",
                    evidence_refs[:4],
                    "Leading-question resistance applied.",
                )
            )
        if analysis_mode == "abstention_check":
            limitations.append(
                self._item(
                    "INSUFFICIENT_EVIDENCE",
                    "No stronger answer is generated because the available context does not support a regulated conclusion.",
                    evidence_refs[:4],
                    "Controlled abstention mode.",
                )
            )
        return limitations

    def _refs_for_evidence(self, evidence: dict[str, Any]) -> list[SourceReference]:
        chunk = next((item for item in evidence.get("chunks", []) if item.get("source_anchor")), None)
        return [
            SourceReference(
                reference_type="EVIDENCE",
                evidence_id=evidence.get("id"),
                evidence_identifier=evidence.get("evidence_identifier"),
                chunk_id=chunk.get("chunk_id") if chunk else None,
                source_anchor=chunk.get("source_anchor", {}) if chunk else {},
                temporal_context=evidence.get("temporal", {}),
            )
        ]

    def _refs_for_observation(self, evidence: dict[str, Any], observation: dict[str, Any]) -> list[SourceReference]:
        refs = self._refs_for_evidence(evidence)
        refs.append(
            SourceReference(
                reference_type="OBSERVATION",
                evidence_id=evidence.get("id"),
                evidence_identifier=evidence.get("evidence_identifier"),
                observation_id=observation.get("observation_id"),
                source_anchor=observation.get("source_anchor", {}) or refs[0].source_anchor,
                temporal_context=evidence.get("temporal", {}),
            )
        )
        return refs

    def _item(self, semantic_type: str, statement: str, refs: list[SourceReference], rationale: str) -> AnalysisItem:
        return AnalysisItem(
            item_id=f"IAI-{uuid.uuid4().hex[:12]}",
            semantic_type=semantic_type,
            statement=statement,
            rationale=rationale,
            source_references=refs,
        )

    def _all_text(self, workspace: InvestigationWorkspaceResponse) -> str:
        parts = [str(workspace.investigation.get("investigation_question", ""))]
        for evidence in workspace.evidence_context:
            parts.extend([str(evidence.get("title", "")), str(evidence.get("evidence_identifier", ""))])
            for chunk in evidence.get("chunks", []):
                parts.append(str(chunk.get("excerpt", "")))
            for obs in evidence.get("observations", []):
                parts.append(str(obs.get("statement", "")))
        return " ".join(parts).lower()

    def _looks_leading(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in ["prove", "confirm", "caused", "root cause", "ignore contradictory", "give me the answer"])
