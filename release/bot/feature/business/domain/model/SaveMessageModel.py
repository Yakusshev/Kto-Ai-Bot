from abc import ABCMeta
from datetime import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from beartype import beartype

from bot.feature.business.domain.model.ForwardOriginState import ForwardOriginState


class MessageRole(StrEnum):
    ASSISTANT = 'assistant'
    USER = 'user'

@dataclass(frozen = True)
class OwnerModel:
    id: int
    username: str
    full_name: str


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
    forward_origin: ForwardOriginState | None


