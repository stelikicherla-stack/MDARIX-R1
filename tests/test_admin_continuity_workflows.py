from datetime import datetime, timedelta, timezone

import pytest

from backend.app.customer_admin_continuity import replacement_action, validate_support_window


def test_last_customer_admin_stays_until_replacement_activates():
    assert replacement_action(0, "INVITED") == "KEEP_CURRENT_UNTIL_ACTIVATED"


def test_active_replacement_allows_incumbent_retirement():
    assert replacement_action(1, "ACTIVE") == "RETIRE_CURRENT"


def test_support_access_must_expire_within_24_hours():
    now = datetime.now(timezone.utc)
    assert "24 hours" in validate_support_window(now + timedelta(minutes=5), now + timedelta(hours=25), now)


def test_support_access_window_is_valid():
    now = datetime.now(timezone.utc)
    assert validate_support_window(now + timedelta(minutes=5), now + timedelta(hours=4), now) is None
