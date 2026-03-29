import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Awaitable
from bot.feature.business.entrypoint.HumanWaitingBehavior import wait_to_see_message
from bot.util.log_util import get_logger


@dataclass
class _StateEntry:
    """Внутренняя запись состояния для одного чата."""
    kind: str  # "preparing" | "answering"
    task: asyncio.Task
    started_at: datetime
    # Корутина для прочтения последнего сообщения обновляется при каждом новом сообщении
    latest_read_coro: Callable[[], Awaitable] | None


class TaskSchedulerRepositoryImpl:
    """
    Конечный автомат (FSM) для управления ответами бота.

    Состояния:
        None          — нет активного диалога (холодный старт)
        "preparing"   — ожидание 10-30 сек (имитация чтения), накапливаем сообщения
        "answering"   — печатаем и генерируем ответ

    Переходы:
        None        + сообщение → "preparing" (сохранить, запустить таймер)
        "preparing" + сообщение → "preparing" (только сохранить, таймер продолжается)
        "answering" + сообщение → "answering" (отменить текущий ответ, ответить сразу)
    """

    __instance = None
    __lock = threading.Lock()
    _states: dict[str, _StateEntry] = {}

    def __new__(cls):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    def is_task_exist(self, key: str) -> bool:
        return key in self._states

    async def cancel_task(
        self,
        key: str,
    ) -> None:
        state = self._states.get(key)
        """Аккуратно отменяет задачу и ждёт её завершения."""
        if state:
            task = state.task
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            self._states.pop(key, None)

    async def on_message(
        self,
        key: str,
        save_coro: Awaitable,
        answer_factory: Callable[[], Awaitable],
        read_message_factory: Callable[[], Awaitable],
    ) -> None:
        """
        Вызывается при каждом входящем сообщении.

        Args:
            key:                 Идентификатор чата
            save_coro:           Сохранить сообщение в БД (выполняется немедленно)
            answer_factory:      Фабрика корутины генерации ответа
            read_message_factory: Фабрика корутины «прочитать сообщение» в Telegram
        """
        # 1. Сохраняем в БД ВСЕГДА и НЕМЕДЛЕННО, до любой логики
        await save_coro

        state = self._states.get(key)

        if state is None:
            # Холодный старт: запускаем фазу подготовки (ожидание 10-30 сек)
            entry = _StateEntry(
                kind = "preparing",
                task = asyncio.create_task(asyncio.sleep(0)),  # placeholder
                started_at = datetime.now(),
                latest_read_coro = read_message_factory,
            )
            self._states[key] = entry
            entry.task = asyncio.create_task(
                self._preparing_flow(key, answer_factory),
            )

        elif state.kind == "preparing":
            # Уже ждём — просто обновляем «последнее» read-действие.
            # Таймер продолжается, все сообщения уже в БД.
            state.latest_read_coro = read_message_factory

        elif state.kind == "answering":
            # Бот уже печатает — отменяем текущий ответ и отвечаем заново
            # на все сообщения (включая только что пришедшее, которое уже в БД)
            await self._cancel_task(state.task)

            # Прочитать новое сообщение сразу
            await read_message_factory()

            entry = _StateEntry(
                kind = "answering",
                task = asyncio.create_task(asyncio.sleep(0)),  # placeholder
                started_at = datetime.now(),
                latest_read_coro = None,
            )
            self._states[key] = entry
            entry.task = asyncio.create_task(
                self._answering_flow(key, answer_factory),
            )

    async def on_remind(
        self,
        key: str,
        answer_factory: Callable[[], Awaitable],
    ) -> None:
        """
        Args:
            key:                 Идентификатор чата
            answer_factory:      Фабрика корутины генерации ответа
        """

        state = self._states.get(key)

        async def empty():
            pass

        if state is not None:
            _logger.warning("on_remind: вызван для диалога, в котором есть активная задача")
            return

        if state is None:
            # Холодный старт: запускаем фазу подготовки (ожидание 10-30 сек)
            entry = _StateEntry(
                kind = "answering",
                task = asyncio.create_task(asyncio.sleep(0)),  # placeholder
                started_at = datetime.now(),
                latest_read_coro = empty,
            )
            self._states[key] = entry
            entry.task = asyncio.create_task(
                self._answering_flow(key, answer_factory),
            )

        elif state.kind == "answering":
            # Бот уже печатает — отменяем текущий ответ и отвечаем заново
            # на все сообщения (включая только что пришедшее, которое уже в БД)
            await self._cancel_task(state.task)

            entry = _StateEntry(
                kind = "answering",
                task = asyncio.create_task(asyncio.sleep(0)),  # placeholder
                started_at = datetime.now(),
                latest_read_coro = None,
            )
            self._states[key] = entry
            entry.task = asyncio.create_task(
                self._answering_flow(key, answer_factory),
            )

    # ------------------------------------------------------------------ #
    #  Внутренние методы FSM                                               #
    # ------------------------------------------------------------------ #

    async def _preparing_flow(
        self,
        key: str,
        answer_factory: Callable[[], Awaitable],
    ) -> None:
        """Ждём 10-30 сек (имитация чтения), затем переходим в answering."""

        try:
            await wait_to_see_message()  # 10-30 сек

            # Помечаем последнее сообщение как прочитанное
            state = self._states.get(key)
            if state and state.latest_read_coro:
                await state.latest_read_coro()

            # Переход: preparing → answering
            if key in self._states:
                entry = self._states[key]
                entry.kind = "answering"
                entry.task = asyncio.create_task(
                    self._answering_flow(key, answer_factory),
                )
                await entry.task

        except asyncio.CancelledError:
            self._states.pop(key, None)
            raise

    async def _answering_flow(
        self,
        key: str,
        answer_factory: Callable[[], Awaitable],
    ) -> None:
        """Генерируем и отправляем ответ, затем сбрасываем состояние."""
        try:
            await answer_factory()
        except asyncio.CancelledError:
            raise
        finally:
            self._states.pop(key, None)

    async def wait_task_completion(self):
        # Собираем все текущие задачи из состояний
        tasks = [entry.task for entry in self._states.values()]
        if tasks:
            # Ждём их завершения, игнорируя исключения (они уже обработаны в самих задачах)
            await asyncio.gather(*tasks, return_exceptions = True)

    @staticmethod
    async def _cancel_task(task: asyncio.Task) -> None:
        """Аккуратно отменяет задачу и ждёт её завершения."""
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

_logger = get_logger(TaskSchedulerRepositoryImpl.__name__)