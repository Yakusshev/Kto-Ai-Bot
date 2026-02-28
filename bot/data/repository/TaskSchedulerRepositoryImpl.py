import asyncio
import threading
from abc import ABC
from asyncio import Task
from dataclasses import dataclass
from datetime import datetime
from typing import Coroutine, Union


class TaskState(ABC):
    task: Task

@dataclass
class Answering(TaskState):
    task: Task

@dataclass
class PreparingForAnswer(TaskState):
    task: Task

# @dataclass
# class Received:
#     time: datetime

class TaskSchedulerRepositoryImpl:
    __instance = None
    __lock = threading.Lock()

    _tasks: dict[str, TaskState] = {}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    def get_state(
        self,
        key: str,
    ) -> TaskState | None:
        return self._tasks.get(key)

    # def has_task(
    #     self,
    #     key: str,
    # ) -> bool:
    #     return self._tasks.get(key) is not None

    # async def set_received_state(
    #     self,
    #     key: str,
    # ):
    #     self._tasks[key] = Received(time = datetime.now())


    async def schedule_preparing_for_answer_task(
        self,
        key: str,
        coroutine: Coroutine,
    ):
        await self.cancel_or_await(key)

        self._tasks[key] = PreparingForAnswer(task = asyncio.create_task(coroutine))

    async def schedule_answering_task(
        self,
        key: str,
        coroutine: Coroutine,
    ):
        await self.cancel_or_await(key)

        self._tasks[key] = Answering(task = asyncio.create_task(coroutine))

    async def cancel_or_await(self, key: str):

        task = self._tasks.pop(key, None).task

        if task and task is PreparingForAnswer:
            await task
        elif task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
