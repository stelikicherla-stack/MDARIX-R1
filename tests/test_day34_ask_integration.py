from types import SimpleNamespace

from backend.app.ask_router import _structured_intelligence


def test_ask_structured_contract_preserves_uncertainty_and_scope():
    result = _structured_intelligence(
        retrieval=SimpleNamespace(
            evidence=({"id": "e1", "provenance": {"source_system": "QMS"}},),
            limitations=("RELATIONSHIPS_ARE_NOT_CAUSAL",),
        ),
        lifecycle={"root_entity": {"product_id": "p1", "product_version_id": "v1"}, "limitations": ["UNREPRESENTED_RELATIONSHIPS_OMITTED"]},
        intelligence={"hypotheses": [{"id": "h1"}], "unknowns": [{"id": "u1"}]},
        spec=SimpleNamespace(temporal_mode=SimpleNamespace(value="CURRENT"), event_start=None, event_end=None, knowledge_time=None),
    )

    assert result["status"] == "READY_FOR_REVIEW"
    assert result["causality_state"] == "NOT_ESTABLISHED"
    assert result["product_scope"] == "p1"
    assert result["product_version_scope"] == "v1"
    assert result["unknowns"] == [{"id": "u1"}]
    assert result["sources_provenance"] == [{"source_system": "QMS"}]
    assert result["human_review_required"] is True


def test_ask_structured_contract_abstains_without_records():
    result = _structured_intelligence(
        retrieval=SimpleNamespace(evidence=(), limitations=()),
        lifecycle=None,
        intelligence=None,
        spec=SimpleNamespace(temporal_mode=SimpleNamespace(value="KNOWN_AS_OF"), event_start=None, event_end=None, knowledge_time=None),
    )

    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["finding"] is None
    assert result["causality_state"] == "NOT_ESTABLISHED"
    assert result["human_review_required"] is False
