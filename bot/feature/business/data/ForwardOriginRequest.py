from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen = True)
class ForwardOriginRequest:
    state: str | None
    datetime: datetime | None
    json: str | None

    @staticmethod
    def empty():
        return ForwardOriginRequest(None, None, None)