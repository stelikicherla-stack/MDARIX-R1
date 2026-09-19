from types import SimpleNamespace
from uuid import uuid4

from evidence.services.evidence_service import build_evidence_summary


def evidence(**overrides):
    values = {
        "id": uuid4(), "evidence_identifier": "EV-DAY33-001", "title": "Source report",
        "fact_type": "source_fact", "source_system": "QMS", "source_reference": "QMS-1",
        "source_timestamp": None, "ingestion_timestamp": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def observation(statement, observation_type="EXPLICIT_SOURCE_STATEMENT", quality_status="VALIDATED", limitations=None):
    return SimpleNamespace(statement=statement, observation_type=observation_type, quality_status=quality_status, limitations=limitations)


def test_day33_preserves_source_and_derived_classification():
    summary = build_evidence_summary(evidence(), [
        observation("Device shut down unexpectedly."),
        observation("Shutdown terminology appears in the source text.", "DETERMINISTIC_DERIVATION"),
    ], uuid4())
    assert summary["facts"] == ["Device shut down unexpectedly."]
    assert summary["derived_observations"] == ["Shutdown terminology appears in the source text."]
    assert summary["source_evidence"][0]["fact_type"] == "source_fact"


def test_day33_marks_partial_and_preserves_limitations():
    summary = build_evidence_summary(evidence(), [observation("Unresolved source reference", quality_status="LIMITATIONS", limitations=[{"code": "MISSING_LOT"}])], uuid4())
    assert summary["sufficiency"] == "PARTIALLY_SUFFICIENT"
    assert summary["unresolved_evidence"] == ["Unresolved source reference"]
    assert summary["limitations"] == [{"code": "MISSING_LOT"}]


def test_day33_empty_evidence_is_insufficient_not_negative():
    summary = build_evidence_summary(evidence(), [], uuid4())
    assert summary["sufficiency"] == "INSUFFICIENT"
    assert summary["facts"] == []
    assert summary["missing_evidence"] == []
