from dataclasses import dataclass
from datetime import datetime

from bot.feature.business.domain.model.SaveMessageModel import MessageRole


@dataclass(frozen = True)
class ChatInfoModel:
    id: int
    business_connection_id: str
    message_count: int
    last_message_date: datetime
    last_message_role: MessageRole
    last_message_content: str