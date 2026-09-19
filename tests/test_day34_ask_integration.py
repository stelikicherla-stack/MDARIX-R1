from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.ask_router import _structured_intelligence, _validate_product_version_scope


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


class _Query:
    def __init__(self, row):
        self.row = row

    def filter(self, *args):
        return self

    def first(self):
        return self.row


class _DB:
    def __init__(self, version, investigation=None):
        self.version = version
        self.investigation = investigation

    def query(self, model):
        return _Query(self.investigation if model.__name__ == "Investigation" else self.version)


def test_product_version_scope_accepts_same_product():
    tenant = uuid4()
    product = uuid4()
    version = uuid4()
    _validate_product_version_scope(
        _DB(SimpleNamespace(id=version, product_id=product)),
        tenant_id=tenant,
        product_version_id=version,
        product_id=product,
        investigation_id=None,
    )


def test_product_version_scope_rejects_incompatible_product():
    tenant = uuid4()
    version = uuid4()
    with pytest.raises(HTTPException) as error:
        _validate_product_version_scope(
            _DB(SimpleNamespace(id=version, product_id=uuid4())),
            tenant_id=tenant,
            product_version_id=version,
            product_id=uuid4(),
            investigation_id=None,
        )
    assert error.value.status_code == 422
    assert error.value.detail["code"] == "PRODUCT_VERSION_SCOPE_MISMATCH"


def test_product_version_scope_hides_foreign_or_unknown_version():
    with pytest.raises(HTTPException) as error:
        _validate_product_version_scope(
            _DB(None),
            tenant_id=uuid4(),
            product_version_id=uuid4(),
            product_id=None,
            investigation_id=None,
        )
    assert error.value.status_code == 404
    assert error.value.detail["code"] == "PRODUCT_VERSION_NOT_FOUND"
