from dataclasses import dataclass


@dataclass(frozen = True)
class MessageForAiModel:
    role: str
    content: str