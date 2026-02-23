from dataclasses import dataclass


@dataclass(frozen = True)
class UserMessageModel:
    id: int
    username: str
    content: str
