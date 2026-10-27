from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from beartype import beartype


class ChatPhase(StrEnum):
    """Фаза диалога бота с одним чатом."""
    IDLE = 'idle'
    PREPARING = 'preparing'
    ANSWERING = 'answering'


@beartype
@dataclass(frozen = True)
class StepTicket:
    """
    «Талон» отложенного шага (прочитать, начать печатать, отправить).

    Выдаётся при планировании шага. Перед действием шаг сверяет талон
    с текущим состоянием чата: если фаза или версия фазы изменились,
    шаг тихо завершается. Так работает отмена без asyncio.Task.cancel.
    """
    chat_id: int
    phase: ChatPhase
    phase_version: int


@beartype
@dataclass(frozen = True)
class ChatState:
    """
    Состояние диалога одного чата (хранится в YDB).

    version - растёт при каждом изменении состояния: новое сообщение пользователя,
    ручной ответ владельца, смена фазы.
    phase_version - значение version на момент начала текущей фазы. Пока в preparing
    копятся сообщения, version растёт, а phase_version (и таймер) остаются прежними.
    pending_message_ids - накопленные сообщения, на которые ещё не ответили.
    """
    chat_id: int
    phase: ChatPhase
    version: int
    phase_version: int
    pending_message_ids: tuple[int, ...]
    updated_at: datetime

    @staticmethod
    def initial(
        chat_id: int,
        now: datetime,
    ) -> 'ChatState':
        """Состояние чата, которого ещё нет в таблице."""
        return ChatState(
            chat_id = chat_id,
            phase = ChatPhase.IDLE,
            version = 0,
            phase_version = 0,
            pending_message_ids = (),
            updated_at = now,
        )

    def ticket(self) -> StepTicket:
        """Талон для отложенного шага текущей фазы."""
        return StepTicket(
            chat_id = self.chat_id,
            phase = self.phase,
            phase_version = self.phase_version,
        )

    def is_actual(
        self,
        ticket: StepTicket,
    ) -> bool:
        """Не устарел ли талон шага относительно этого состояния."""
        return self.chat_id == ticket.chat_id \
            and self.phase == ticket.phase \
            and self.phase_version == ticket.phase_version
