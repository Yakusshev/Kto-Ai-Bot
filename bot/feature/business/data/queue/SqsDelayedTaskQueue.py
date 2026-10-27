import asyncio
import math
from dataclasses import dataclass
from typing import Any

import boto3

from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.repository.DelayedTaskQueue import (
    MAX_DELAY_SECONDS,
    DelayedTaskQueue,
)
from bot.util.log_util import get_logger


@dataclass(frozen = True)
class SqsConfig:
    endpoint: str
    region: str
    access_key_id: str
    secret_access_key: str
    queue_url: str


def create_sqs_client(
    config: SqsConfig,
) -> Any:
    """Клиент SQS API (Yandex Message Queue совместима по протоколу)."""
    return boto3.client(
        'sqs',
        endpoint_url = config.endpoint,
        region_name = config.region,
        aws_access_key_id = config.access_key_id,
        aws_secret_access_key = config.secret_access_key,
    )


class SqsDelayedTaskQueue(DelayedTaskQueue):
    """
    Отложенные шаги через SQS API (Yandex Message Queue).

    Задержка - DelaySeconds сообщения; предел очереди 900 сек (MAX_DELAY_SECONDS).
    Наши паузы короче: до 30 сек «прочитал», «печатает» после чтения не дольше
    предела (длинное сообщение обрезается до 900), остальное - внутри шага.
    Большее значение обрезается до предела с предупреждением в логе, задача не теряется.

    Ожидания от инфраструктуры (задаются при создании очередей, не в коде):
        очередь недоставленных (DLQ) и redrive policy с maxReceiveCount = 3-5:
        шаг, который падает (например, недоступна YDB), после этого уйдёт в DLQ;
        visibility timeout больше самого долгого шага (генерация + паузы, от 120 сек),
        иначе шаг доставится второй раз, пока первая доставка ещё работает.
    Приём сообщений и вызов HandleChatStepUseCase - задача приёмника (S2/S6).
    """

    def __init__(
        self,
        client: Any,
        queue_url: str,
    ):
        self._client = client
        self._queue_url = queue_url

    async def send(
        self,
        task: ChatStepPayload,
        delay_seconds: float | int,
    ) -> None:
        delay = math.ceil(max(delay_seconds, 0))
        if delay > MAX_DELAY_SECONDS:
            _logger.warning(
                "Задержка %s сек выше предела очереди, обрезана до %s: %s",
                delay, MAX_DELAY_SECONDS, task.step_id,
            )
            delay = MAX_DELAY_SECONDS

        # boto3 синхронный: не блокируем event loop
        await asyncio.to_thread(
            self._client.send_message,
            QueueUrl = self._queue_url,
            MessageBody = task.to_json(),
            DelaySeconds = delay,
        )


_logger = get_logger(SqsDelayedTaskQueue.__name__)
