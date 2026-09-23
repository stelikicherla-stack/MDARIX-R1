from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    text: str
    category: str = "TRANSACTIONAL"
    reply_to: str | None = None


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> str: ...

    def health(self) -> dict[str, object]: ...
