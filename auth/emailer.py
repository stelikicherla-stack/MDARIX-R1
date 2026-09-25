from __future__ import annotations

import os
import smtplib
from email.utils import parseaddr
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


class EmailDeliveryError(RuntimeError):
    """Controlled SMTP failure that never includes credentials or raw protocol data."""


def smtp_configuration_status() -> dict[str, object]:
    required = {
        "host": os.getenv("MDARIX_SMTP_HOST"),
        "username": os.getenv("MDARIX_SMTP_USERNAME"),
        "password": os.getenv("MDARIX_SMTP_PASSWORD"),
        "sender": os.getenv("MDARIX_SMTP_FROM"),
    }
    return {
        "configured": all(required.values()),
        "present": {name: bool(value) for name, value in required.items()},
        "port_present": bool(os.getenv("MDARIX_SMTP_PORT")),
        "app_url_present": bool(os.getenv("MDARIX_APP_URL")),
        "sender_domain_verified": bool(os.getenv("MDARIX_SMTP_VERIFIED_DOMAIN")) and parseaddr(required["sender"] or "")[1].endswith("@" + os.getenv("MDARIX_SMTP_VERIFIED_DOMAIN", "")),
    }


def _send_link_email(recipient: str, token: str, *, subject: str, path: str, intro: str) -> str:
    """Send a controlled account link when SMTP is configured.

    Returns a delivery state so callers never claim an email was sent when the
    host has no configured mail provider.
    """
    host = os.getenv("MDARIX_SMTP_HOST")
    username = os.getenv("MDARIX_SMTP_USERNAME")
    password = os.getenv("MDARIX_SMTP_PASSWORD")
    sender = os.getenv("MDARIX_SMTP_FROM")
    if not all((host, username, password, sender)):
        return "NOT_CONFIGURED"
    verified_domain = os.getenv("MDARIX_SMTP_VERIFIED_DOMAIN")
    if verified_domain and not parseaddr(sender)[1].endswith("@" + verified_domain):
        raise EmailDeliveryError("SMTP sender domain is not verified")

    app_url = os.getenv("MDARIX_APP_URL", "http://127.0.0.1:5178")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"{intro}\n\n"
        f"{app_url}{path}?token={token}\n\n"
        "This link expires in one hour."
    )
    port = int(os.getenv("MDARIX_SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.starttls()
            client.login(username, password)
            client.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryError("SMTP delivery failed. Verify the sender address, Gmail App Password, and network access.") from exc
    return "SENT"


def send_verification_email(recipient: str, token: str) -> str:
    return _send_link_email(
        recipient,
        token,
        subject="Verify your MDARIX email address",
        path="/verify-email",
        intro="Verify your MDARIX account by opening this link:",
    )


def send_activation_email(recipient: str, token: str, organization: str) -> str:
    return _send_link_email(
        recipient,
        token,
        subject="Activate your MDARIX account",
        path="/activate-account",
        intro=f"You have been invited to MDARIX for {organization}. Create your password here:",
    )


def send_password_reset_email(recipient: str, token: str) -> str:
    return _send_link_email(
        recipient,
        token,
        subject="Reset your MDARIX password",
        path="/reset-password",
        intro="Reset your MDARIX password by opening this link:",
    )
