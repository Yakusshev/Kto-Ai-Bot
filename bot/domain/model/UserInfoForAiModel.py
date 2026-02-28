from dataclasses import dataclass


@dataclass(frozen = True)
class UserInfoForAiModel:
    id: int
    username: str
