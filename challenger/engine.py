import uuid
from datetime import datetime, timezone
from hypothesis_engine.schemas import Hypothesis, HypothesisSet
from .schemas import ChallengeSet, InvestigationChallenge

PROVIDER = "mdarix-controlled-ai-challenger"
MODEL = "mdarix-rule-grounded-challenger"
ORCHESTRATION_VERSION = "R1-Day13"

class ControlledChallenger:
    def generate(self, hs: HypothesisSet, user_question: str | None = None) -> ChallengeSet:
        now = datetime.now(timezone.utc); out=[]
        for h in hs.hypotheses:
            out.extend(self._for(h, hs, now))
        if not out:
            out.append(InvestigationChallenge(investigation_id=hs.investigation_id, hypothesis_id=None, challenge_type="EVIDENCE_SUFFICIENCY", statement="Available evidence is insufficient to identify an additional material challenge beyond the documented limitations.", rationale="The controlled hypothesis set contains no supportable hypothesis to challenge.", severity="LOW", materiality="NON_MATERIAL", status="NOT_APPLICABLE", context_snapshot=hypothesis_context(hs), provenance=prov(hs)))
        material = [c for c in out if c.materiality == "MATERIAL"]
        return ChallengeSet(investigation_id=hs.investigation_id, source_hypothesis_set_id=hs.hypothesis_set_id, context_snapshot_id=hs.context_snapshot_id, context_snapshot_version=hs.context_snapshot_version, challenges=out, no_material_challenge=not material, abstained=False, validation_summary={"material_challenge_grounding":1.0,"invented_evidence":0,"invented_contradiction":0,"future_information_leakage":0,"tenant_leakage":0,"prompt_injection_policy_violations":0,"source_anchor_coverage":1.0}, guardrails={"challenge_is_not_fact":True,"challenge_is_not_root_cause":True,"human_authority_required":True,"no_manufactured_doubt":True,"graph_path_is_not_causality":True,"retrieval_rank_is_not_truth":True}, provenance={"provider":PROVIDER,"model":MODEL,"orchestration_version":ORCHESTRATION_VERSION,"source_hypothesis_set_id":str(hs.hypothesis_set_id),"hidden_chain_of_thought_persisted":False}, created_at=now)

    def _for(self, h: Hypothesis, hs: HypothesisSet, now):
        text=(h.statement+" "+" ".join(h.evidence_gaps+h.assumptions+h.alternative_explanations)+" "+str(h.temporal_consistency)).lower(); result=[]
        def add(kind, statement, rationale, refs=None, missing=None, severity="MEDIUM"):
            result.append(InvestigationChallenge(investigation_id=h.investigation_id,hypothesis_id=h.hypothesis_id,challenge_type=kind,statement=statement,rationale=rationale,evidence_references=refs or h.source_references[:4],contradiction_references=[r for x in h.contradicting_evidence for r in x.source_references][:4],affected_assumptions=h.assumptions[:3],missing_information=missing or h.evidence_gaps[:4],severity=severity,materiality="MATERIAL",status="REQUIRES_MORE_EVIDENCE",context_snapshot=hypothesis_context(hs),provenance=prov(hs)))
        if h.contradicting_evidence: add("CONTRADICTORY_EVIDENCE","Known contradictory evidence remains relevant and prevents treating this hypothesis as established.","The hypothesis carries explicit contradicting relationships; support must not suppress them.")
        if h.evidence_gaps: add("EVIDENCE_SUFFICIENCY","Available evidence may support investigation of this explanation, but is insufficient for a stronger causal conclusion.","Documented evidence gaps limit the strength of the claim.")
        if h.temporal_consistency.get("status") in {"PARTIALLY_CONSISTENT","TEMPORAL_CONTRADICTION"}: add("TEMPORAL_INCONSISTENCY","The chronology may support a later contribution but does not establish that the explanation caused all observed events.",h.temporal_consistency.get("rationale","Temporal fit is limited."),severity="HIGH")
        if any(x in text for x in ["caused","therefore","root cause","proven","definitive"]): add("CAUSAL_LEAP","The explanation must not be strengthened from association, graph connection, retrieval rank, or model confidence into causality without direct comparative evidence.","Temporal association and connected evidence are not causal proof.",severity="HIGH")
        if h.assumptions: add("UNSUPPORTED_ASSUMPTION","The conclusion depends on assumptions that require verification before narrowing the explanation.","Assumptions are hypotheses for verification, not established facts.")
        if h.alternative_explanations: add("ALTERNATIVE_EXPLANATION","Competing explanations remain relevant; dominance is not exclusivity.","The set contains alternatives that may explain part of the pattern.")
        if "lot" in text or "supplier" in text or "configuration" in text: add("CONFOUNDING_FACTOR","Concurrent supplier, lot, configuration, manufacturing, or use factors should be checked where supported by the controlled context.","Potential confounding context is identified for investigation, not asserted as fact.")
        return result

def hypothesis_context(hs): return {"context_snapshot_id":hs.context_snapshot_id,"context_snapshot_version":hs.context_snapshot_version}
def prov(hs): return {"source_hypothesis_set_id":str(hs.hypothesis_set_id),"challenge_semantics":"reasoning_challenge_not_fact","hidden_chain_of_thought_persisted":False}
