from abc import ABCMeta, ABC
from dataclasses import dataclass
from datetime import datetime

from beartype import beartype


@beartype
@dataclass(frozen = True)
class ForwardOriginState(ABC):
    date: datetime

    USER = "user"
    HIDDEN_USER = "hidden_user"
    CHAT = "chat"
    CHANNEL = "channel"

@beartype
@dataclass(frozen = True)
class ForwardOriginUserModel(ForwardOriginState):
    id: int
    bot: bool
    username: str
    full_name: str

@beartype
@dataclass(frozen = True)
class ForwardOriginHiddenUserModel(ForwardOriginState):
    username: str

@beartype
@dataclass(frozen = True)
class ForwardOriginChatModel(ForwardOriginState):
    pass

@beartype
@dataclass(frozen = True)
class ForwardOriginChannelModel(ForwardOriginState):
    id: int
    title: str
    username: str
    message_id: int
