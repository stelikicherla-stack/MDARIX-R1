import pytest

from backend.app.customer_lifecycle import LIFECYCLE_TRANSITIONS, allowed_lifecycle_transition


def test_lifecycle_matrix_contains_all_governed_states():
    expected = {"DRAFT", "PENDING_APPROVAL", "PROVISIONING", "PROVISIONED", "PENDING_CUSTOMER_ACTIVATION", "ACTIVE", "EXPIRING_SOON", "EXPIRED", "SUSPENDED", "TERMINATED", "ARCHIVED"}
    assert set(LIFECYCLE_TRANSITIONS) == expected


@pytest.mark.parametrize("current,target", [
    ("DRAFT", "PENDING_APPROVAL"),
    ("PENDING_APPROVAL", "PROVISIONING"),
    ("PROVISIONING", "PROVISIONED"),
    ("PROVISIONED", "PENDING_CUSTOMER_ACTIVATION"),
    ("PENDING_CUSTOMER_ACTIVATION", "ACTIVE"),
    ("ACTIVE", "SUSPENDED"),
    ("SUSPENDED", "ACTIVE"),
    ("ACTIVE", "EXPIRING_SOON"),
    ("EXPIRING_SOON", "EXPIRED"),
    ("EXPIRED", "TERMINATED"),
    ("TERMINATED", "ARCHIVED"),
])
def test_allowed_lifecycle_transitions(current, target):
    assert allowed_lifecycle_transition(current, target)


def test_every_unlisted_transition_is_rejected():
    for current, targets in LIFECYCLE_TRANSITIONS.items():
        for target in LIFECYCLE_TRANSITIONS:
            if target not in targets:
                assert not allowed_lifecycle_transition(current, target), f"unexpected transition {current}->{target}"


def test_unknown_states_are_denied_by_default():
    assert not allowed_lifecycle_transition("UNKNOWN", "ACTIVE")
    assert not allowed_lifecycle_transition("ACTIVE", "UNKNOWN")
    assert not allowed_lifecycle_transition("ARCHIVED", "ACTIVE")
