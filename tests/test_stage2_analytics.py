from types import SimpleNamespace

from backend.app.stage3_router import persona_dashboard, signals_summary


def _ctx():
    return SimpleNamespace(tenant_id="tenant-a", user_id="user-a")


class EmptyDB:
    def execute(self, *args, **kwargs):
        return self

    def rollback(self):
        pass

    def __iter__(self):
        return iter(())

    def scalar(self):
        return 0


def test_signals_are_tenant_scoped_and_limited_when_optional_data_is_missing():
    result = signals_summary(EmptyDB(), _ctx())
    assert result["tenant_id"] == "tenant-a"
    assert result["signals"] == []
    assert result["limitations"]


def test_persona_dashboard_preserves_tenant_and_human_review():
    result = persona_dashboard("executive", EmptyDB(), _ctx())
    assert result["status"] == "READY_FOR_REVIEW"
    assert result["tenant_id"] == "tenant-a"
    assert result["human_review_required"] is True
