from dataclasses import dataclass

from beartype import beartype


@beartype
@dataclass(frozen = True)
class UserInfoForAiModel:
    id: int
    username: str
