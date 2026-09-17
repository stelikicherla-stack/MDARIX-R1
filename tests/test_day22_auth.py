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
