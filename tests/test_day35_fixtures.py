from access_control.fixtures import FIXTURE_TENANTS, FIXTURE_USERS, validate_fixture


def test_day35_fixture_has_four_tenants_and_twenty_five_users():
    validate_fixture()
    assert len(FIXTURE_TENANTS) == 4
    assert len(FIXTURE_USERS) == 25


def test_day35_fixture_users_are_tenant_bound_and_unique():
    tenant_keys = {tenant.key for tenant in FIXTURE_TENANTS}
    assert all(user.tenant_key in tenant_keys for user in FIXTURE_USERS)
    assert len({user.email for user in FIXTURE_USERS}) == 25
