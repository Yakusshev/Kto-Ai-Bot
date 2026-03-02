from dataclasses import dataclass

from beartype import beartype
from datetime import datetime


@beartype
@dataclass(frozen = True)
class UserMessageInfoForAiModel:
    id: int
    username: str
    full_name: str
    datetime: datetime
