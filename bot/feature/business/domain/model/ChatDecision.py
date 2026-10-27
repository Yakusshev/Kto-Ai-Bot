from dataclasses import dataclass
from enum import StrEnum

from beartype import beartype

from bot.feature.business.domain.model.ChatState import ChatState


class ChatAction(StrEnum):
    """Что должен сделать вызывающий код после перехода."""
    NONE = 'none'  # ничего: сообщение лишь накоплено, таймер идёт
    START_PREPARING = 'start_preparing'  # запустить таймер «чтения» (10-30 сек)
    START_ANSWER = 'start_answer'  # начать ответ
    CANCEL_AND_ANSWER_NOW = 'cancel_and_answer_now'  # прочитать сразу и ответить на всё
    CANCEL = 'cancel'  # ответ отменён (владелец ответил сам)
    STALE = 'stale'  # событие устарело, состояние не менялось


@beartype
@dataclass(frozen = True)
class ChatDecision:
    state: ChatState
    action: ChatAction
