from dataclasses import dataclass

from beartype import beartype

from bot.domain.model.SaveMessageModel import SaveMessageModel


@beartype
@dataclass(frozen = True)
class PendingChat:
    messages: list[SaveMessageModel]
    last_message_time: float