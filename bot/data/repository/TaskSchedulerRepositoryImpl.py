import asyncio
import threading
from typing import Coroutine

from bot.domain.model.SaveMessageModel import SaveMessageModel


class TaskSchedulerRepositoryImpl:
    __instance = None
    __lock = threading.Lock()

    _tasks: dict[str, asyncio.Task] = {}
    _message_queue_dict: dict[str, list[SaveMessageModel]] = {}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    async def schedule_task(
        self,
        key: str,
        save_message_model: SaveMessageModel,
        coroutine: Coroutine,
    ):
        message_list = self._message_queue_dict[key]
        self._message_queue_dict[key] = message_list.__add__([save_message_model])
        await self.cancel(key)

        async def _wrapper():
            await coroutine

        self._tasks[key] = asyncio.create_task(_wrapper())

    async def cancel(self, key: str):
        task = self._tasks.pop(key, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
