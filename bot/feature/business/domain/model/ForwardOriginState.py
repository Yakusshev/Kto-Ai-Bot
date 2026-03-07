from abc import ABCMeta, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Union

from beartype import beartype

USER = "user"
HIDDEN_USER = "hidden_user"
CHAT = "chat"
CHANNEL = "channel"


@beartype
@dataclass(frozen = True)
class ForwardOriginUserModel:
    date: datetime
    id: int
    bot: bool
    username: str
    full_name: str

@beartype
@dataclass(frozen = True)
class ForwardOriginHiddenUserModel:
    date: datetime
    username: str

@beartype
@dataclass(frozen = True)
class ForwardOriginChatModel:
    date: datetime
    pass

@beartype
@dataclass(frozen = True)
class ForwardOriginChannelModel:
    date: datetime
    id: int
    title: str
    username: str
    message_id: int


ForwardOriginState = Union[
    ForwardOriginUserModel,
    ForwardOriginHiddenUserModel,
    ForwardOriginChatModel,
    ForwardOriginChannelModel,
]
