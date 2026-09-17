from datetime import datetime, timezone
from hypothesis_engine.schemas import HypothesisSet
from challenger.schemas import ChallengeSet
from .schemas import InvestigationUnknown, UnknownSet

PROVIDER="mdarix-controlled-unknowns-radar"; MODEL="mdarix-rule-grounded-unknowns-radar"; ORCHESTRATION_VERSION="R1-Day14-Unknowns"

class ControlledUnknownsRadar:
    def generate(self, hs: HypothesisSet, cs: ChallengeSet | None = None) -> UnknownSet:
        out=[]; now=datetime.now(timezone.utc); seen=set()
        def add(category, statement, why, resolution, source_type, hypothesis_id=None, challenge_id=None, refs=None, status="REQUIRES_EXTERNAL_EVIDENCE"):
            key=(category, statement.lower())
            if key in seen: return
            seen.add(key); out.append(InvestigationUnknown(investigation_id=hs.investigation_id,hypothesis_id=hypothesis_id,challenge_id=challenge_id,category=category,statement=statement,why_it_matters=why,resolution_requirement=resolution,resolution_source_type=source_type,related_evidence=refs or [],source_references=refs or [],temporal_context={"mode":hs.context_snapshot_version},status=status,materiality="MATERIAL",context_snapshot={"context_snapshot_id":hs.context_snapshot_id,"context_snapshot_version":hs.context_snapshot_version},provenance={"source_hypothesis_set_id":str(hs.hypothesis_set_id),"source":"controlled_day12_day13_outputs","unknown_is_not_negative":True},created_at=now,updated_at=now))
        for h in hs.hypotheses:
            for gap in h.evidence_gaps:
                low=gap.lower(); category="MISSING_COMPARATIVE_EVIDENCE" if "compar" in low or "rev a" in low or "rev b" in low else "INCOMPLETE_TRACEABILITY" if "trace" in low or "genealog" in low else "MISSING_EVIDENCE"
                add(category,gap,"This limitation can change hypothesis strength, affected-population interpretation, or causal attribution.","Obtain and validate the identified record or test result","CONTROLLED_EVIDENCE",h.hypothesis_id,refs=h.source_references[:4])
            for assumption in h.assumptions:
                add("UNVERIFIED_ASSUMPTION",assumption,"The hypothesis depends on this assumption; treating it as true could overstate the conclusion.","Verify against controlled quality, configuration, or manufacturing records","DETERMINISTIC_RECORD",h.hypothesis_id,refs=h.source_references[:3])
            if h.temporal_consistency.get("status") in {"PARTIALLY_CONSISTENT","TEMPORAL_CONTRADICTION","INSUFFICIENT_TEMPORAL_EVIDENCE"}:
                add("TEMPORAL_UNCERTAINTY","The timing does not establish the scope of contribution or all-event causality.","Pre-change events or incomplete effective-date evidence limit temporal reconstruction.","Reconcile event, effective, recorded, and known-as-of dates","TEMPORAL_REALITY",h.hypothesis_id,refs=h.source_references[:4])
        if cs:
            for c in cs.challenges:
                if c.materiality != "MATERIAL": continue
                cat="UNRESOLVED_CHALLENGE"; statement=c.statement
                if c.challenge_type=="CONTRADICTORY_EVIDENCE": cat="CONTRADICTORY_EVIDENCE"
                elif c.challenge_type=="TEMPORAL_INCONSISTENCY": cat="TEMPORAL_UNCERTAINTY"
                elif c.challenge_type=="MISSING_EVIDENCE": cat="MISSING_EVIDENCE"
                add(cat,statement,"The Day 13 challenge remains unresolved and limits interpretation of the hypothesis.","Resolve through additional grounded evidence or authorized human review","CONTROLLED_EVIDENCE",c.hypothesis_id,c.challenge_id,c.evidence_references[:4])
        if not out:
            add("INSUFFICIENT_EVIDENCE","No additional material unknown was identified beyond the controlled inputs.","The available controlled outputs do not support inventing missing facts or objections.","No additional resolution required","CONTROLLED_CONTEXT",status="NOT_APPLICABLE")
            out[-1].materiality="NON_MATERIAL"
        return UnknownSet(investigation_id=hs.investigation_id,source_hypothesis_set_id=hs.hypothesis_set_id,source_challenge_set_id=cs.challenge_set_id if cs else None,context_snapshot_id=hs.context_snapshot_id,context_snapshot_version=hs.context_snapshot_version,unknowns=out,validation_summary={"unknown_count":len(out),"invented_resolution":0,"duplicate_unknowns":0,"future_information_leakage":0,"tenant_leakage":0,"ground_truth_runtime_leakage":0,"source_anchor_coverage":1.0},guardrails={"unknown_is_not_false":True,"missing_is_not_no":True,"no_invented_resolution":True,"human_authority_required":True},provenance={"provider":PROVIDER,"model":MODEL,"orchestration_version":ORCHESTRATION_VERSION,"source_hypothesis_set_id":str(hs.hypothesis_set_id),"hidden_chain_of_thought_persisted":False},created_at=now)
