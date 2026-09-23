import json
import os
from urllib.request import Request, urlopen
from .provider import EmailMessage


class ResendProvider:
    endpoint = "https://api.resend.com/emails"

    def __init__(self, api_key: str | None = None, sender: str | None = None, reply_to: str | None = None):
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.sender = sender or os.getenv("RESEND_FROM_EMAIL")
        self.reply_to = reply_to or os.getenv("RESEND_REPLY_TO")

    def health(self) -> dict[str, object]:
        return {"provider": "resend", "configured": bool(self.api_key and self.sender),
                "api_key_present": bool(self.api_key), "sender_present": bool(self.sender),
                "reply_to_present": bool(self.reply_to)}

    def send(self, message: EmailMessage) -> str:
        if not self.api_key or not self.sender:
            raise RuntimeError("RESEND_NOT_CONFIGURED")
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
