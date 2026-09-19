from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from scenario_intelligence.schemas import ScenarioRequest


def scenario(**overrides):
    values = {
        "scenario_type": "EXCLUDE_RELATIONSHIP",
        "question": "What changes if Component Rev B is excluded?",
        "target": "Component Rev B",
    }
    values.update(overrides)
    return ScenarioRequest(**values)


def test_controlled_scenario_types_and_temporal_modes():
    assert scenario().scenario_type == "EXCLUDE_RELATIONSHIP"
    assert scenario(temporal_mode="event", as_of=datetime(2026, 2, 15, tzinfo=timezone.utc)).temporal_mode == "event"
    assert scenario(temporal_mode="known", as_of=datetime(2026, 2, 15, tzinfo=timezone.utc)).temporal_mode == "known"


def test_current_rejects_cutoff_and_historical_requires_one():
    with pytest.raises(ValidationError):
        scenario(as_of=datetime.now(timezone.utc))
    with pytest.raises(ValidationError):
        scenario(temporal_mode="known")


def test_arbitrary_scenario_code_is_not_an_input():
    with pytest.raises(ValidationError):
        scenario(scenario_type="DROP_TABLE")


def test_product_version_scope_is_explicit_and_persistence_is_opt_in():
    item = scenario(product_version_id=uuid4(), persist=False)
    assert item.product_version_id is not None
    assert item.persist is False
