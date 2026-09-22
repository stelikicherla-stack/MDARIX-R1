from datetime import datetime, timezone
from auth.emailer import send_activation_email, smtp_configuration_status, EmailDeliveryError
from auth.durable import hash_token, persist_session, issue_reset, consume
from backend.app.db.models.stage2 import AuthSession, PasswordResetRequest

def test_smtp_status_reports_required_production_configuration(monkeypatch):
    for key, value in {
        'MDARIX_SMTP_HOST': 'smtp.example.test', 'MDARIX_SMTP_USERNAME': 'sender@example.test',
        'MDARIX_SMTP_PASSWORD': 'app-secret', 'MDARIX_SMTP_FROM': 'sender@example.test',
        'MDARIX_SMTP_PORT': '587', 'MDARIX_APP_URL': 'https://app.example.test'
    }.items(): monkeypatch.setenv(key, value)
    status = smtp_configuration_status()
    assert status['configured'] is True and status['port_present'] and status['app_url_present']

def test_smtp_delivery_uses_tls_auth_and_message(monkeypatch):
    for key, value in {'MDARIX_SMTP_HOST':'smtp.example.test','MDARIX_SMTP_USERNAME':'sender@example.test','MDARIX_SMTP_PASSWORD':'app-secret','MDARIX_SMTP_FROM':'sender@example.test','MDARIX_APP_URL':'https://app.example.test'}.items(): monkeypatch.setenv(key,value)
    events=[]
    class FakeSMTP:
        def __init__(self, host, port, timeout): events.append(('connect',host,port,timeout))
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def starttls(self): events.append(('starttls',))
        def login(self, username, password): events.append(('login',username,password))
        def send_message(self, message): events.append(('send',message['To'],message['Subject']))
    monkeypatch.setattr('auth.emailer.smtplib.SMTP', FakeSMTP)
    assert send_activation_email('customer@example.test','token-value','Customer') == 'SENT'
    assert ('starttls',) in events and ('login','sender@example.test','app-secret') in events

def test_smtp_failure_is_controlled_and_secret_free(monkeypatch):
    for key, value in {'MDARIX_SMTP_HOST':'smtp.example.test','MDARIX_SMTP_USERNAME':'sender@example.test','MDARIX_SMTP_PASSWORD':'super-secret','MDARIX_SMTP_FROM':'sender@example.test'}.items(): monkeypatch.setenv(key,value)
    class BrokenSMTP:
        def __init__(self,*args,**kwargs): raise OSError('network detail')
    monkeypatch.setattr('auth.emailer.smtplib.SMTP', BrokenSMTP)
    try: send_activation_email('customer@example.test','token-value','Customer')
    except EmailDeliveryError as exc: assert 'super-secret' not in str(exc) and 'network detail' not in str(exc)
    else: raise AssertionError('SMTP failure was not raised')

def test_durable_token_hash_is_one_way():
    assert hash_token('raw-token') != 'raw-token' and hash_token('raw-token') == hash_token('raw-token')
