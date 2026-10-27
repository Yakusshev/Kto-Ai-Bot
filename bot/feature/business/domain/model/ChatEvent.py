from dataclasses import dataclass
from enum import StrEnum

from beartype import beartype

from bot.feature.business.domain.model.ChatState import StepTicket


class ChatEventKind(StrEnum):
    USER_MESSAGE = 'user_message'  # новое сообщение пользователя
    OWNER_MESSAGE = 'owner_message'  # ручной ответ владельца
    REMIND = 'remind'  # напоминание: ответить без входящего сообщения
    PREPARING_FINISHED = 'preparing_finished'  # «прочитал» и пора отвечать
    ANSWER_FINISHED = 'answer_finished'  # ответ отправлен


@beartype
@dataclass(frozen = True)
class ChatEvent:
    """
    Событие диалога.
    message_id - у событий с сообщением (USER_MESSAGE, OWNER_MESSAGE).
    ticket - у событий отложенных шагов (PREPARING_FINISHED, ANSWER_FINISHED).
    """
    kind: ChatEventKind
    message_id: int | None = None
    ticket: StepTicket | None = None
