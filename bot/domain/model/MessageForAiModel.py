from dataclasses import dataclass

from bot.domain.model.SaveMessageModel import MessageRole


@dataclass(frozen = True)
class MessageForAiModel:
    role: MessageRole
    content: str