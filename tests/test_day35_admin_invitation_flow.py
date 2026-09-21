from pathlib import Path


ROOT = Path(__file__).parents[1]
ACCESS_ROUTER = (ROOT / "backend" / "app" / "access_router.py").read_text(encoding="utf-8")
AUTH_ROUTER = (ROOT / "backend" / "app" / "auth_router.py").read_text(encoding="utf-8")
EMAILER = (ROOT / "auth" / "emailer.py").read_text(encoding="utf-8")
UI = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")


def test_admin_invite_does_not_collect_or_store_admin_visible_password():
    assert "[\"password\", \"Temporary password\"" not in UI
    assert "password_hash=_hash(payload.password)" not in ACCESS_ROUTER
    assert "USER_INVITATION_SENT" in ACCESS_ROUTER
    assert "send_activation_email" in ACCESS_ROUTER
    assert "development_token" in ACCESS_ROUTER


def test_frontend_navigation_recognizes_platform_and_customer_admin_roles():
    assert "PLATFORM_ADMIN" in UI
    assert "CUSTOMER_ADMIN" in UI
    assert "MDARIX ADMINISTRATOR" in UI


def test_activation_and_reset_have_dedicated_routes_and_email_links():
    assert "\"/activate-account\"" in UI
    assert "\"/reset-password\"" in UI
    assert "@router.post('/activate-account')" in AUTH_ROUTER
    assert "@router.post('/reset-password')" in AUTH_ROUTER
    assert "send_password_reset_email" in AUTH_ROUTER
    assert "Activate your MDARIX account" in EMAILER
    assert "Reset your MDARIX password" in EMAILER


def test_customer_and_platform_admin_controls_are_server_side():
    assert "PLATFORM_ADMIN_REQUIRED" in ACCESS_ROUTER
    assert "CUSTOMER_ADMIN_LIMIT_REACHED" in ACCESS_ROUTER
    assert "LICENSED_USER_LIMIT_REACHED" in ACCESS_ROUTER
    assert "PLATFORM_ROLE_NOT_ALLOWED" in ACCESS_ROUTER
    assert "FOREIGN_TENANT_ACCESS_DENIED" in ACCESS_ROUTER
    assert '@router.post("/platform-admin/customers")' in ACCESS_ROUTER


def test_smtp_configuration_uses_environment_and_never_embeds_secret_values():
    assert "MDARIX_SMTP_HOST" in EMAILER
    assert "MDARIX_SMTP_PASSWORD" in EMAILER
    assert "client.login(username, password)" in EMAILER
    assert "Temp@1234password" not in EMAILER
    assert "Globe#270707" not in EMAILER
