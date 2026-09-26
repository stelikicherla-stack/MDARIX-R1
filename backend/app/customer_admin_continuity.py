"""Pure continuity rules shared by the customer-admin workflow and tests."""

from datetime import datetime, timedelta


def replacement_action(active_other_admins: int, replacement_status: str) -> str:
    """Only retire the incumbent after a different active admin exists."""
    if active_other_admins > 0 and replacement_status.upper() == "ACTIVE":
        return "RETIRE_CURRENT"
    return "KEEP_CURRENT_UNTIL_ACTIVATED"


def validate_support_window(starts_at: datetime, expires_at: datetime, now: datetime) -> str | None:
    if starts_at < now - timedelta(minutes=1):
        return "Support access must have a future start"
    if expires_at <= starts_at:
        return "Support access expiry must be after its start"
    if expires_at - starts_at > timedelta(hours=24):
        return "Support access may not exceed 24 hours"
    return None
