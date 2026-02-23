import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen = True)
class SaveMessageModel:
    chat_id: int
    created_at: datetime
    message_id: int
    role: str
    content: str
    event_type: str
    reply_to_id: int
    text_quote: Optional[str]
    business_connection_id: str
