import uuid
from datetime import datetime, timezone
from challenger.engine import ControlledChallenger
from challenger.schemas import ChallengeSet
from hypothesis_engine.schemas import Hypothesis, HypothesisSet

def hs(**kw):
    now=datetime.now(timezone.utc); h=Hypothesis(hypothesis_id=uuid.uuid4(),investigation_id=uuid.uuid4(),statement=kw.get('statement','Rev B caused the shutdown increase'),scope='test',status='MIXED_EVIDENCE',contradicting_evidence=kw.get('contradicting',[]),assumptions=['complaint coding remained consistent'],evidence_gaps=kw.get('gaps',['comparative testing unavailable']),alternative_explanations=['lot variation'],temporal_consistency={'status':'PARTIALLY_CONSISTENT','rationale':'complaints existed before Rev B'},context_snapshot={},provenance={},created_at=now,updated_at=now)
    return HypothesisSet(hypothesis_set_id=uuid.uuid4(),investigation_id=h.investigation_id,source_analysis_id=uuid.uuid4(),context_snapshot_id='ctx',context_snapshot_version='R1-Day10',status='MIXED_EVIDENCE',hypotheses=[h],validation_summary={},guardrails={},provenance={},created_at=now)

def test_challenger_preserves_boundaries_and_temporal_issue():
    result=ControlledChallenger().generate(hs())
    kinds={c.challenge_type for c in result.challenges}
    assert {'EVIDENCE_SUFFICIENCY','TEMPORAL_INCONSISTENCY','CAUSAL_LEAP','UNSUPPORTED_ASSUMPTION','ALTERNATIVE_EXPLANATION'} <= kinds
    assert result.validation_summary['invented_evidence']==0
    assert all(c.provenance['challenge_semantics']=='reasoning_challenge_not_fact' for c in result.challenges)

def test_abstention_is_not_forced_into_contradiction():
    now=datetime.now(timezone.utc); base=hs(); base.hypotheses[0].evidence_gaps=[]; base.hypotheses[0].assumptions=[]; base.hypotheses[0].alternative_explanations=[]; base.hypotheses[0].temporal_consistency={'status':'CONSISTENT'}; base.hypotheses[0].statement='A supported explanation'
    result=ControlledChallenger().generate(base)
    assert result.challenges
    assert result.no_material_challenge is True
