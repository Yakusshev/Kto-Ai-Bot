import asyncio

import pytest

from bot.feature.business.data.queue.InMemoryDelayedTaskQueue import \
    InMemoryDelayedTaskQueue
from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket
from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from ...domain.fake.ChatStepHarness import make_context


def _payload(step_id: str) -> ChatStepPayload:
    return ChatStepPayload(
        step_id = step_id,
        kind = ChatStepKind.READ_MESSAGE,
        ticket = StepTicket(chat_id = 5, phase = ChatPhase.PREPARING, phase_version = 3),
        context = make_context(),
    )


class TestInMemoryDelayedTaskQueue:

    @pytest.fixture
    def handled(self) -> list[str]:
        return []

    @pytest.fixture
    def queue(self, handled: list[str]) -> InMemoryDelayedTaskQueue:
        async def handler(payload: ChatStepPayload) -> None:
            handled.append(payload.step_id)

        return InMemoryDelayedTaskQueue(handler = handler)

    @pytest.mark.asyncio
    async def test_when_delayed_expect_handler_called_not_earlier_and_in_delay_order(
        self,
        queue: InMemoryDelayedTaskQueue,
        handled: list[str],
    ):
        await queue.send(task = _payload("late"), delay_seconds = 0.08)
        await queue.send(task = _payload("early"), delay_seconds = 0.01)

        await asyncio.sleep(0.04)
        assert handled == ["early"]

        await asyncio.sleep(0.08)
        assert handled == ["early", "late"]

    @pytest.mark.asyncio
    async def test_when_handler_fails_expect_other_steps_still_run(
        self,
        handled: list[str],
    ):
        async def handler(payload: ChatStepPayload) -> None:
            if payload.step_id == "bad":
                raise RuntimeError("boom")
            handled.append(payload.step_id)

        queue = InMemoryDelayedTaskQueue(handler = handler)

        await queue.send(task = _payload("bad"), delay_seconds = 0)
        await queue.send(task = _payload("good"), delay_seconds = 0.01)
        await asyncio.sleep(0.05)

        assert handled == ["good"]

    @pytest.mark.asyncio
    async def test_when_shutdown_expect_running_step_finished_and_scheduled_dropped(
        self,
        handled: list[str],
    ):
        started = asyncio.Event()

        async def handler(payload: ChatStepPayload) -> None:
            started.set()
            await asyncio.sleep(0.05)
            handled.append(payload.step_id)

        queue = InMemoryDelayedTaskQueue(handler = handler)
        await queue.send(task = _payload("running"), delay_seconds = 0)
        await queue.send(task = _payload("scheduled"), delay_seconds = 0.2)
        await started.wait()

        await queue.shutdown()
        await asyncio.sleep(0.25)

        assert handled == ["running"]

    @pytest.mark.asyncio
    async def test_when_send_after_shutdown_expect_dropped(
        self,
        queue: InMemoryDelayedTaskQueue,
        handled: list[str],
    ):
        await queue.shutdown()

        await queue.send(task = _payload("x"), delay_seconds = 0)
        await asyncio.sleep(0.02)

        assert handled == []
