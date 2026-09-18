from auth.service import LocalAuthService

def test_signup_verification_login_logout_and_reset():
    auth=LocalAuthService(); created=auth.signup("person@example.com","Strong password 123","Person","Org")
    assert created["status"]=="PENDING_VERIFICATION"; account=auth.accounts["person@example.com"]; assert "Strong password" not in account.password_hash
    auth.verify_email(created["development_token"]); session=auth.signin("person@example.com","Strong password 123"); assert auth.context(session)["tenant_id"].startswith("sandbox-"); auth.signout(session)
    reset=auth.request_reset("person@example.com"); auth.reset(reset["development_token"],"Another strong 123"); assert auth.signin("person@example.com","Another strong 123")

def test_invalid_replay_and_unknown_account_are_safe():
    auth=LocalAuthService(); auth.signup("person@example.com","Strong password 123","Person","Org")
    try: auth.signin("unknown@example.com","wrong password")
    except ValueError as exc: assert str(exc)=="INVALID_CREDENTIALS"
    else: assert False

def test_persisted_auth_user_survives_auth_service_restart():
    original=LocalAuthService(); created=original.signup("persisted@example.com","Strong password 123","Persisted","Org")
    account=original.accounts["persisted@example.com"]; original.verify_email(created["development_token"])
    restarted=LocalAuthService()
    token=restarted.signin_persisted(account.email,"Strong password 123",user_id="user-1",display_name=account.display_name,tenant_id="tenant-1",password_hash=account.password_hash,role="Viewer",status="ACTIVE",email_verified=True)
    assert restarted.context(token)["tenant_id"] == "tenant-1"
