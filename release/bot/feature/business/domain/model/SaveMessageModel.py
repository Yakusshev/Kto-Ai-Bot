from datetime import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from beartype import beartype


class MessageRole(StrEnum):
    ASSISTANT = 'assistant'
    USER = 'user'

@beartype
@dataclass(frozen = True)
class SaveMessageModel:
    chat_id: int
    created_at: datetime
    message_id: int
    role: MessageRole
    content: str
    event_type: str
    reply_to_id: int | None
    text_quote: Optional[str]
    business_connection_id: str
