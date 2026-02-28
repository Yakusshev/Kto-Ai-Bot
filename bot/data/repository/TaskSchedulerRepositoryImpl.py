import asyncio
import threading
from abc import ABC
from asyncio import Task
from dataclasses import dataclass
from datetime import datetime
from typing import Coroutine, Union

from aiogram.fsm.state import StatesGroup


@dataclass(frozen = True)
class TaskModel(StatesGroup):
    preparing_date_time: datetime
    preparingTask: Task
    answeringTask: Task | None


class TaskState(ABC):
    datetime: datetime

@dataclass
class PreparingForAnswer(TaskState):
    datetime: datetime

@dataclass
class Answering(TaskState):
    datetime: datetime

# @dataclass
# class Received:
#     time: datetime

class TaskSchedulerRepositoryImpl:
    __instance = None
    __lock = threading.Lock()

    _tasks: dict[str, TaskModel] = {}

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

        task_model = self._tasks.get(key)

        if task_model:
            if task_model.answeringTask:
                return Answering(task_model.preparing_date_time)
            else:
                return PreparingForAnswer(task_model.preparing_date_time)
        else:
            return None

    async def handle(
        self,
        key: str,
        prepare: Coroutine,
        answer: Coroutine,
    ):
        task_model = self._tasks.get(key)

        if task_model:

        else:
            self._tasks[key] = TaskModel(
                preparing_date_time = datetime.now(),
                preparingTask = asyncio.create_task(prepare),
                answeringTask = None,
            )

        await self._tasks[key].preparingTask



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
