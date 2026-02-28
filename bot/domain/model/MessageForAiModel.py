from dataclasses import dataclass

from beartype import beartype

from bot.domain.model.SaveMessageModel import MessageRole


@beartype
@dataclass(frozen = True)
class MessageForAiModel:
    role: MessageRole
    content: str