import asyncio
from collections.abc import Awaitable, Callable

from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.repository.DelayedTaskQueue import (
    MAX_DELAY_SECONDS,
    DelayedTaskQueue,
)
from bot.util.log_util import get_logger

StepHandler = Callable[[ChatStepPayload], Awaitable[None]]


class InMemoryDelayedTaskQueue(DelayedTaskQueue):
    """
    Очередь в памяти процесса (asyncio, call_later): режим polling и тесты.
    Шаги выполняются в этом же процессе тем же обработчиком, что получит приёмник SQS.

    Остановка (shutdown): ещё не начатые шаги отбрасываются (в SQS они остались бы
    в очереди), запущенные - дожидаются. Чат, у которого шаг отброшен, остаётся в
    фазе preparing/answering в YDB; её снимает следующее сообщение или таймаут зависшей
    фазы (DecideChatTransitionUseCase).
    """

    def __init__(
        self,
        handler: StepHandler,
    ):
        self._handler = handler
        self._timer_map: dict[str, asyncio.TimerHandle] = {}
        self._running_set: set[asyncio.Task[None]] = set()
        self._is_closed = False

    async def send(
        self,
        task: ChatStepPayload,
        delay_seconds: float | int,
    ) -> None:
        if self._is_closed:
            _logger.warning("Очередь остановлена, шаг отброшен: %s", task.step_id)
            return

        # Те же ограничения, что у SQS: поведение режимов не расходится
        delay = min(max(delay_seconds, 0), MAX_DELAY_SECONDS)

        self._timer_map[task.step_id] = asyncio.get_running_loop().call_later(
            delay,
            self._start,
            task,
        )

    async def shutdown(self) -> None:
        self._is_closed = True

        for timer in self._timer_map.values():
            timer.cancel()
        _logger.info("Остановка очереди: отброшено не начатых шагов - %s", len(self._timer_map))
        self._timer_map.clear()

        if self._running_set:
            await asyncio.gather(*self._running_set, return_exceptions = True)

    def _start(
        self,
        task: ChatStepPayload,
    ) -> None:
        self._timer_map.pop(task.step_id, None)
        running = asyncio.create_task(self._run(task = task))
        self._running_set.add(running)
        running.add_done_callback(self._running_set.discard)

    async def _run(
        self,
        task: ChatStepPayload,
    ) -> None:
        try:
            await self._handler(task)
        except Exception:
            _logger.exception("Ошибка шага %s: chat_id=%s", task.kind, task.chat_id)


_logger = get_logger(InMemoryDelayedTaskQueue.__name__)
