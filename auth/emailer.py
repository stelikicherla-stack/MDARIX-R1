from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_verification_email(recipient: str, token: str) -> str:
    """Send the verification link when SMTP is configured.

    Returns a delivery state so callers never claim an email was sent when the
    host has no configured mail provider.
    """
    host = os.getenv("MDARIX_SMTP_HOST")
    username = os.getenv("MDARIX_SMTP_USERNAME")
    password = os.getenv("MDARIX_SMTP_PASSWORD")
    sender = os.getenv("MDARIX_SMTP_FROM")
    if not all((host, username, password, sender)):
        return "NOT_CONFIGURED"

    app_url = os.getenv("MDARIX_APP_URL", "http://127.0.0.1:5178")
    message = EmailMessage()
    message["Subject"] = "Verify your MDARIX email address"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "Verify your MDARIX account by opening this link:\n\n"
        f"{app_url}/verify-email?token={token}\n\n"
        "This link expires in one hour."
    )
    port = int(os.getenv("MDARIX_SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as client:
        client.starttls()
        client.login(username, password)
        client.send_message(message)
    return "SENT"
