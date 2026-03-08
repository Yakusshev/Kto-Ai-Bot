from abc import ABC
from dataclasses import dataclass
from datetime import datetime

class ForwardOriginState(ABC):
    date: datetime

@dataclass(frozen = True)
class ForwardOriginUserModel(ForwardOriginState):
    date: datetime
    id: int
    bot: bool
    username: str
    full_name: str

@dataclass(frozen = True)
class ForwardOriginHiddenUserModel(ForwardOriginState):
    date: datetime
    full_name: str

@dataclass(frozen = True)
class ForwardOriginChatModel(ForwardOriginState):
    date: datetime
    id: int
    title: str
    username: str

@dataclass(frozen = True)
class ForwardOriginChannelModel(ForwardOriginState):
    date: datetime
    id: int
    title: str
    username: str
    # username может быть пустым
    message_id: int
