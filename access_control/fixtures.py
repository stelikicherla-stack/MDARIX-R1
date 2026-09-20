"""Deterministic R1 identity fixture catalogue.

The catalogue is data-only: provisioning is deliberately separate so tests
can validate tenant boundaries without silently changing a live database.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FixtureUser:
    key: str
    email: str
    tenant_key: str
    role: str
    personas: tuple[str, ...]


@dataclass(frozen=True)
class FixtureTenant:
    key: str
    name: str


FIXTURE_TENANTS = tuple(
    FixtureTenant(f"R1_TENANT_{index}", name)
    for index, name in enumerate(("Northstar Quality", "Aster Medical", "Nimbus Health", "Orbit Devices"), 1)
)

_ROLE_PERSONAS = (
    ("Administrator", ("ADMINISTRATOR",)),
    ("Investigator", ("INVESTIGATOR",)),
    ("Reviewer", ("REVIEWER",)),
    ("Approver", ("APPROVER",)),
    ("Leader", ("LEADER",)),
)

FIXTURE_USERS = tuple(
    FixtureUser(
        key=f"R1_USER_{index:02d}",
        email=f"r1-user-{index:02d}@synthetic.invalid",
        tenant_key=FIXTURE_TENANTS[(index - 1) % len(FIXTURE_TENANTS)].key,
        role=_ROLE_PERSONAS[(index - 1) % len(_ROLE_PERSONAS)][0],
        personas=_ROLE_PERSONAS[(index - 1) % len(_ROLE_PERSONAS)][1],
    )
    for index in range(1, 26)
)


def validate_fixture() -> None:
    tenant_keys = {tenant.key for tenant in FIXTURE_TENANTS}
    if len(tenant_keys) != 4 or len(FIXTURE_USERS) != 25:
        raise ValueError("R1_FIXTURE_CARDINALITY_INVALID")
    if any(user.tenant_key not in tenant_keys for user in FIXTURE_USERS):
        raise ValueError("R1_FIXTURE_TENANT_REFERENCE_INVALID")
    if len({user.email for user in FIXTURE_USERS}) != len(FIXTURE_USERS):
        raise ValueError("R1_FIXTURE_EMAIL_NOT_UNIQUE")


validate_fixture()
