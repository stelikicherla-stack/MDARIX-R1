from .provider import EmailMessage, EmailProvider
from .resend_provider import ResendProvider


class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        self.provider = provider or ResendProvider()

    def send_template(self, recipient: str, template: str, values: dict[str, str], *, category: str = "TRANSACTIONAL") -> str:
        subjects = {"activation": "Activate your MDARIX account", "password_reset": "Reset your MDARIX password", "invitation": "You are invited to MDARIX", "evidence_request": "MDARIX evidence request", "renewal_60": "Your MDARIX subscription renewal is approaching", "renewal_30": "Your MDARIX subscription renews soon", "renewal_7": "Action required: MDARIX subscription renewal"}
        subject = subjects.get(template, "MDARIX notification")
        link = values.get("link", "")
        text = f"{values.get('intro', 'MDARIX notification')}\n\n{link}\n\nThis message requires human review where applicable."
        return self.provider.send(EmailMessage(recipient, subject, text, category))
