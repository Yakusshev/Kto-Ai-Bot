import pytest

from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket
from bot.feature.business.domain.model.ChatStep import (
    ChatStepKind,
    ChatStepPayload,
)
from bot.feature.business.domain.repository.DelayedTaskQueue import MAX_DELAY_SECONDS
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase
from bot.feature.business.domain.util.HumanDelays import HumanDelays
from ..fake.ChatStepHarness import make_context
from ..fake.FakeDelayedTaskQueue import FakeDelayedTaskQueue

PREPARING = StepTicket(chat_id = 1, phase = ChatPhase.PREPARING, phase_version = 1)
ANSWERING = StepTicket(chat_id = 1, phase = ChatPhase.ANSWERING, phase_version = 1)


def _use_case(is_instant: bool) -> tuple[ScheduleChatStepUseCase, FakeDelayedTaskQueue]:
    queue = FakeDelayedTaskQueue()
    return ScheduleChatStepUseCase(
        delayed_task_queue = queue,
        human_delays = HumanDelays(is_instant = is_instant),
    ), queue


class TestDelays:

    @pytest.mark.asyncio
    async def test_when_debug_typing_expect_all_delays_zero(self):
        use_case, queue = _use_case(is_instant = True)
        long_text = "слово " * 500

        for kind, ticket in (
            (ChatStepKind.READ_MESSAGE, PREPARING),
            (ChatStepKind.START_TYPING, ANSWERING),
            (ChatStepKind.GENERATE_AND_SEND, ANSWERING),
        ):
            await use_case.invoke(
                kind = kind,
                ticket = ticket,
                context = make_context(text = long_text),
            )

        assert [delay for _, delay in queue.sent_list] == [0, 0, 0]
        assert HumanDelays(is_instant = True).write_message("текст " * 100) == 0

    @pytest.mark.asyncio
    async def test_when_preparing_read_expect_delay_10_to_30(self):
        use_case, queue = _use_case(is_instant = False)

        for _ in range(20):
            await use_case.invoke(
                kind = ChatStepKind.READ_MESSAGE,
                ticket = PREPARING,
                context = make_context(),
            )

        assert all(10 <= delay <= 30 for _, delay in queue.sent_list)

    @pytest.mark.asyncio
    async def test_when_read_in_answering_expect_immediate(self):
        use_case, queue = _use_case(is_instant = False)

        await use_case.invoke(
            kind = ChatStepKind.READ_MESSAGE,
            ticket = ANSWERING,
            context = make_context(),
        )
        await use_case.invoke(
            kind = ChatStepKind.GENERATE_AND_SEND,
            ticket = ANSWERING,
            context = make_context(),
        )

        assert [delay for _, delay in queue.sent_list] == [0, 0]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("да", 2.0),
            ("слово " * 30, 20.0),
            ("слово " * 5000, MAX_DELAY_SECONDS),
        ],
        ids = ["short", "thirty_words", "huge_capped_by_queue_limit"],
    )
    async def test_when_start_typing_expect_read_time_within_queue_limit(
        self,
        text: str,
        expected: float,
    ):
        use_case, queue = _use_case(is_instant = False)

        await use_case.invoke(
            kind = ChatStepKind.START_TYPING,
            ticket = ANSWERING,
            context = make_context(text = text),
        )

        assert queue.sent_list[0][1] == expected

    def test_when_write_expect_at_least_minimum_pause(self):
        delays = HumanDelays(is_instant = False)

        assert delays.write_message("да") == 1.5
        assert 100 / 6 <= delays.write_message("а" * 100) <= 100 / 2


class TestPayload:

    @pytest.mark.asyncio
    async def test_when_serialized_expect_equal_after_roundtrip(self):
        use_case, queue = _use_case(is_instant = True)
        await use_case.invoke(
            kind = ChatStepKind.START_TYPING,
            ticket = ANSWERING,
            context = make_context(text = "тест «юникод»"),
        )
        payload = queue.payload_list[0]

        assert ChatStepPayload.from_json(payload.to_json()) == payload

    def test_when_unknown_version_expect_error(self):
        with pytest.raises(ValueError):
            ChatStepPayload.from_json('{"v": 99}')
