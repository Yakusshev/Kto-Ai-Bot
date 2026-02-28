import asyncio
import threading
from typing import Coroutine


class TaskSchedulerRepositoryImpl:
    __instance = None
    __lock = threading.Lock()

    _tasks: dict[str, asyncio.Task] = {}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    def has_task(
        self,
        key: str,
    ) -> bool:
        return self._tasks.get(key) is None

    async def schedule_task(
        self,
        key: str,
        coroutine: Coroutine,
    ):
        await self.__cancel(key)

        async def _wrapper():
            await coroutine

        self._tasks[key] = asyncio.create_task(_wrapper())

    async def __cancel(self, key: str):
        task = self._tasks.pop(key, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
