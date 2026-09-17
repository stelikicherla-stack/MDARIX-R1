import json
from datetime import datetime
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parents[1] / "evaluation" / "fixtures" / "nimbus_productversion_temporal_applicability.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def eligible(record, version, mode, cutoff):
    if record.get("tenant") not in (None, "ACME_CARE_SYNTHETIC"):
        return False
    if record["version"] not in (None, version):
        return False
    if mode == "current":
        return True
    timestamp = record["event"] if mode == "event" else record["known"]
    return datetime.fromisoformat(timestamp) <= cutoff


@pytest.mark.parametrize("version,mode,expected_present,expected_absent", [
    ("A", "current", {"NV-A-EVID-PRE","NV-A-EVID-POST","NV-SHARED-EVID-PRE","NV-LATE-KNOWN","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE"}, {"NV-B-EVID-PRE","NV-B-EVID-POST","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE","NV-B-GRAPH-POST","NV-FOREIGN-EVID-PRE"}),
    ("A", "event", {"NV-A-EVID-PRE","NV-SHARED-EVID-PRE","NV-LATE-KNOWN","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE"}, {"NV-A-EVID-POST","NV-B-EVID-PRE","NV-B-EVID-POST","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE","NV-B-GRAPH-POST","NV-FOREIGN-EVID-PRE"}),
    ("A", "known", {"NV-A-EVID-PRE","NV-SHARED-EVID-PRE","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE"}, {"NV-A-EVID-POST","NV-LATE-KNOWN","NV-B-EVID-PRE","NV-B-EVID-POST","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE","NV-B-GRAPH-POST","NV-FOREIGN-EVID-PRE"}),
    ("B", "current", {"NV-B-EVID-PRE","NV-B-EVID-POST","NV-SHARED-EVID-PRE","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE","NV-B-GRAPH-POST"}, {"NV-A-EVID-PRE","NV-A-EVID-POST","NV-LATE-KNOWN","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE","NV-FOREIGN-EVID-PRE"}),
    ("B", "event", {"NV-B-EVID-PRE","NV-SHARED-EVID-PRE","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE"}, {"NV-B-EVID-POST","NV-A-EVID-PRE","NV-A-EVID-POST","NV-LATE-KNOWN","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE","NV-B-GRAPH-POST","NV-FOREIGN-EVID-PRE"}),
    ("B", "known", {"NV-B-EVID-PRE","NV-SHARED-EVID-PRE","NV-B-CHANGE-PRE","NV-B-GRAPH-PRE"}, {"NV-B-EVID-POST","NV-A-EVID-PRE","NV-A-EVID-POST","NV-LATE-KNOWN","NV-A-CHANGE-PRE","NV-A-GRAPH-PRE","NV-B-GRAPH-POST","NV-FOREIGN-EVID-PRE"}),
])
def test_six_cell_positive_and_negative_applicability(version, mode, expected_present, expected_absent):
    fixture = load_fixture()
    cutoff = datetime.fromisoformat(fixture["cutoff"])
    actual = {record["key"] for record in fixture["records"] if eligible(record, version, mode, cutoff)}
    assert expected_present <= actual
    assert expected_absent.isdisjoint(actual)


def test_event_and_known_exact_late_known_difference():
    fixture = load_fixture()
    cutoff = datetime.fromisoformat(fixture["cutoff"])
    late = next(record for record in fixture["records"] if record["key"] == "NV-LATE-KNOWN")
    assert eligible(late, "A", "event", cutoff)
    assert not eligible(late, "A", "known", cutoff)


def test_shared_and_foreign_controls():
    fixture = load_fixture()
    cutoff = datetime.fromisoformat(fixture["cutoff"])
    for version in ("A", "B"):
        assert "NV-SHARED-EVID-PRE" in {r["key"] for r in fixture["records"] if eligible(r, version, "event", cutoff)}
        assert "NV-FOREIGN-EVID-PRE" not in {r["key"] for r in fixture["records"] if eligible(r, version, "event", cutoff)}


def test_fixture_has_no_duplicate_business_keys():
    keys = [record["key"] for record in load_fixture()["records"]]
    assert len(keys) == len(set(keys))
