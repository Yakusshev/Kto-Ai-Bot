from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen = True)
class ForwardOriginSerializationModel:
    state: str | None
    datetime: datetime | None
    json: str | None

    @staticmethod
    def empty():
        return ForwardOriginSerializationModel(None, None, None)