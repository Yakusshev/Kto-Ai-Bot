from dataclasses import dataclass

from bot.domain.model.SaveMessageModel import SaveMessageModel


@dataclass(frozen = True)
class PendingChat:
    messages: list[SaveMessageModel]
    last_message_time: float