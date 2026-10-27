import uuid

from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket
from bot.feature.business.domain.model.ChatStep import (
    ChatStepContext,
    ChatStepKind,
    ChatStepPayload,
)
from bot.feature.business.domain.repository.DelayedTaskQueue import DelayedTaskQueue
from bot.feature.business.domain.util.HumanDelays import HumanDelays


class ScheduleChatStepUseCase:
    """
    Ставит отложенный шаг в очередь. Задержку определяет вид шага:
        прочитать (фаза preparing) - 10-30 сек, «прочитал» после паузы;
        прочитать (фаза answering) - сразу: отмена прежнего ответа и ответ на всё;
        начать печатать - время прочитать сообщение;
        сгенерировать и отправить - сразу.
    """

    def __init__(
        self,
        delayed_task_queue: DelayedTaskQueue,
        human_delays: HumanDelays,
    ):
        self._queue = delayed_task_queue
        self._delays = human_delays

    async def invoke(
        self,
        kind: ChatStepKind,
        ticket: StepTicket,
        context: ChatStepContext,
    ) -> None:
        payload = ChatStepPayload(
            step_id = uuid.uuid4().hex,
            kind = kind,
            ticket = ticket,
            context = context,
        )
        await self._queue.send(
            task = payload,
            delay_seconds = self._delay_seconds(
                kind = kind,
                ticket = ticket,
                context = context,
            ),
        )

    def _delay_seconds(
        self,
        kind: ChatStepKind,
        ticket: StepTicket,
        context: ChatStepContext,
    ) -> float:
        if kind == ChatStepKind.READ_MESSAGE and ticket.phase == ChatPhase.PREPARING:
            return self._delays.see_message()
        if kind == ChatStepKind.START_TYPING:
            return self._delays.start_typing(message_text = context.message_text)
        return 0.0
