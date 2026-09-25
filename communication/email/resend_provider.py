import json
import os
from email.utils import parseaddr
from urllib.request import Request, urlopen
from .provider import EmailMessage


class ResendProvider:
    endpoint = "https://api.resend.com/emails"

    def __init__(self, api_key: str | None = None, sender: str | None = None, reply_to: str | None = None):
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.sender = sender or os.getenv("RESEND_FROM_EMAIL")
        self.reply_to = reply_to or os.getenv("RESEND_REPLY_TO")

    def health(self) -> dict[str, object]:
        sender_domain = parseaddr(self.sender or "")[1].split("@")[-1] if "@" in parseaddr(self.sender or "")[1] else ""
        verified_domain = os.getenv("RESEND_VERIFIED_DOMAIN", "")
        return {"provider": "resend", "configured": bool(self.api_key and self.sender and (not verified_domain or sender_domain == verified_domain)),
                "api_key_present": bool(self.api_key), "sender_present": bool(self.sender),
                "reply_to_present": bool(self.reply_to), "sender_domain": sender_domain,
                "verified_domain_configured": bool(verified_domain), "sender_domain_verified": bool(sender_domain and (not verified_domain or sender_domain == verified_domain))}

    def send(self, message: EmailMessage) -> str:
        if not self.api_key or not self.sender:
            raise RuntimeError("RESEND_NOT_CONFIGURED")
        verified_domain = os.getenv("RESEND_VERIFIED_DOMAIN")
        sender_domain = parseaddr(self.sender)[1].split("@")[-1] if "@" in parseaddr(self.sender)[1] else ""
        if verified_domain and sender_domain != verified_domain:
            raise RuntimeError("RESEND_SENDER_DOMAIN_NOT_VERIFIED")
        payload = {"from": self.sender, "to": [message.recipient], "subject": message.subject, "text": message.text}
        reply_to = message.reply_to or self.reply_to
        if reply_to:
            payload["reply_to"] = [reply_to]
        request = Request(self.endpoint, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode() or "{}")
        except Exception as exc:
            raise RuntimeError("RESEND_DELIVERY_FAILED") from exc
        return str(data.get("id", "SENT"))
