from unittest.mock import MagicMock

import pytest

from bot.feature.business.data.queue.SqsDelayedTaskQueue import (
    SqsConfig,
    SqsDelayedTaskQueue,
    create_sqs_client,
)
from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket
from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from bot.feature.business.domain.repository.DelayedTaskQueue import MAX_DELAY_SECONDS
from ...domain.fake.ChatStepHarness import make_context

QUEUE_URL = "https://message-queue.api.cloud.yandex.net/b1g/dq/steps"


def _payload() -> ChatStepPayload:
    return ChatStepPayload(
        step_id = "abc",
        kind = ChatStepKind.READ_MESSAGE,
        ticket = StepTicket(chat_id = 5, phase = ChatPhase.PREPARING, phase_version = 3),
        context = make_context(text = "привет"),
    )


@pytest.fixture
def client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def queue(client: MagicMock) -> SqsDelayedTaskQueue:
    return SqsDelayedTaskQueue(client = client, queue_url = QUEUE_URL)


class TestSqsDelayedTaskQueue:

    @pytest.mark.asyncio
    async def test_when_send_expect_body_queue_and_delay_passed(
        self,
        queue: SqsDelayedTaskQueue,
        client: MagicMock,
    ):
        payload = _payload()

        await queue.send(task = payload, delay_seconds = 12.3)

        client.send_message.assert_called_once_with(
            QueueUrl = QUEUE_URL,
            MessageBody = payload.to_json(),
            DelaySeconds = 13,
        )
        sent_body = client.send_message.call_args.kwargs["MessageBody"]
        assert ChatStepPayload.from_json(sent_body) == payload

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "delay, expected",
        [(0, 0), (-5, 0), (900, 900), (901, 900), (5000.5, 900)],
    )
    async def test_when_delay_out_of_range_expect_clamped_to_queue_limit(
        self,
        queue: SqsDelayedTaskQueue,
        client: MagicMock,
        delay: float | int,
        expected: int,
    ):
        await queue.send(task = _payload(), delay_seconds = delay)

        actual = client.send_message.call_args.kwargs["DelaySeconds"]
        assert actual == expected
        assert 0 <= actual <= MAX_DELAY_SECONDS == 900

    @pytest.mark.asyncio
    async def test_when_client_fails_expect_error_propagated(
        self,
        queue: SqsDelayedTaskQueue,
        client: MagicMock,
    ):
        client.send_message.side_effect = RuntimeError("queue down")

        with pytest.raises(RuntimeError):
            await queue.send(task = _payload(), delay_seconds = 1)

    def test_when_create_client_expect_yandex_endpoint_and_region(self):
        client = create_sqs_client(
            config = SqsConfig(
                endpoint = "https://message-queue.api.cloud.yandex.net",
                region = "ru-central1",
                access_key_id = "key",
                secret_access_key = "secret",
                queue_url = QUEUE_URL,
            ),
        )

        assert client.meta.endpoint_url == "https://message-queue.api.cloud.yandex.net"
        assert client.meta.region_name == "ru-central1"
