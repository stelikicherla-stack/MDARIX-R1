import pytest

from access_control.personas import R1_PERSONAS, get_persona, validate_persona_assignments


def test_r1_contains_exactly_six_canonical_personas():
    assert len(R1_PERSONAS) == 6
    assert {persona.code for persona in R1_PERSONAS} == {
        "INVESTIGATOR", "PRODUCT_QUALITY", "REVIEWER", "APPROVER", "LEADER", "ADMINISTRATOR"
    }


def test_persona_lookup_is_normalized():
    assert get_persona(" reviewer ").label == "Regulatory/PMS Reviewer"


def test_unknown_persona_is_rejected():
    with pytest.raises(ValueError, match="UNKNOWN_PERSONA"):
        get_persona("SUPERUSER")


def test_duplicate_persona_assignment_is_rejected():
    with pytest.raises(ValueError, match="DUPLICATE_PERSONA"):
        validate_persona_assignments(["INVESTIGATOR", "investigator"])
