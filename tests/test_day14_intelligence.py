import uuid
from datetime import datetime, timezone
from hypothesis_engine.schemas import Hypothesis, HypothesisSet
from challenger.schemas import ChallengeSet
from unknowns.engine import ControlledUnknownsRadar
from failure_chain.engine import ControlledFailureChain

def inputs():
    now=datetime.now(timezone.utc); iid=uuid.uuid4()
    h=Hypothesis(hypothesis_id=uuid.uuid4(),investigation_id=iid,statement='Component Rev B may contribute to later shutdown increase',scope='component',status='MIXED_EVIDENCE',assumptions=['genealogy is complete'],evidence_gaps=['Comparative Rev A / Rev B testing unavailable','Lot traceability incomplete'],alternative_explanations=['Manufacturing variation'],temporal_consistency={'status':'PARTIALLY_CONSISTENT','rationale':'Pre-change complaints exist'},context_snapshot={},provenance={},created_at=now,updated_at=now)
    hs=HypothesisSet(hypothesis_set_id=uuid.uuid4(),investigation_id=iid,source_analysis_id=uuid.uuid4(),context_snapshot_id='ctx',context_snapshot_version='R1-Day10',status='MIXED_EVIDENCE',hypotheses=[h],validation_summary={},guardrails={},provenance={},created_at=now)
    cs=ChallengeSet(investigation_id=iid,source_hypothesis_set_id=hs.hypothesis_set_id,context_snapshot_id='ctx',context_snapshot_version='R1-Day10',guardrails={},provenance={},created_at=now)
    return hs,cs

def test_unknowns_are_first_class_and_deduplicated():
    hs,cs=inputs(); result=ControlledUnknownsRadar().generate(hs,cs)
    categories={u.category for u in result.unknowns}
    assert 'MISSING_COMPARATIVE_EVIDENCE' in categories
    assert 'INCOMPLETE_TRACEABILITY' in categories
    assert all(u.materiality=='MATERIAL' for u in result.unknowns)
    assert result.validation_summary['invented_resolution']==0
    assert result.validation_summary['duplicate_unknowns']==0

def test_failure_chain_preserves_broken_link_and_never_claims_causality():
    hs,cs=inputs(); unknowns=ControlledUnknownsRadar().generate(hs,cs); result=ControlledFailureChain().generate(hs,unknowns)
    chain=result.chains[0]
    assert chain.overall_status=='BROKEN_CHAIN'
    assert any(link.epistemic_status=='UNKNOWN_GAP' for link in chain.links)
    assert chain.unresolved_links
    assert result.validation_summary['invented_links']==0
    assert result.guardrails['graph_path_is_not_causality'] is True
    assert all(link.provenance['causal_claim'] is False for link in chain.links)

def test_unknown_is_not_negative_and_empty_chain_abstains():
    hs,cs=inputs(); hs.hypotheses=[]; result=ControlledFailureChain().generate(hs)
    assert result.chains[0].overall_status=='ABSTAINED'
    unknowns=ControlledUnknownsRadar().generate(hs,cs)
    assert unknowns.unknowns[0].category=='INSUFFICIENT_EVIDENCE'
    assert unknowns.unknowns[0].materiality=='NON_MATERIAL'
