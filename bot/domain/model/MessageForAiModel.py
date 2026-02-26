from dataclasses import dataclass


@dataclass(frozen = True)
class MessageForAiModel:
    id: int
    username: str
    content: str
