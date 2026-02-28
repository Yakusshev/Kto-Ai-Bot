from datetime import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

class MessageRole(StrEnum):
    ASSISTANT = 'assistant'
    USER = 'user'

@dataclass(frozen = True)
class SaveMessageModel:
    chat_id: int
    created_at: datetime
    message_id: int
    role: MessageRole
    content: str
    event_type: str
    reply_to_id: int
    text_quote: Optional[str]
    business_connection_id: str
