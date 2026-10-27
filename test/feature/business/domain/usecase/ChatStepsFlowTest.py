import asyncio

import pytest

from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatState import ChatPhase
from bot.feature.business.domain.model.ChatStep import ChatStepKind
from ..fake.ChatStepHarness import CHAT_ID, ChatStepHarness, make_context


@pytest.fixture
def harness() -> ChatStepHarness:
    return ChatStepHarness()


async def _phase(harness: ChatStepHarness) -> ChatPhase:
    return (await harness.state_repository.get(chat_id = CHAT_ID)).phase


class TestSteps:

    @pytest.mark.asyncio
    async def test_when_message_expect_read_then_typing_then_one_answer(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)

        await harness.run_all()

        assert [p.kind for p in harness.queue.payload_list] == [
            ChatStepKind.READ_MESSAGE,
            ChatStepKind.START_TYPING,
            ChatStepKind.GENERATE_AND_SEND,
        ]
        assert harness.bot.sent_text_list == ["ответ"]
        assert harness.bot.count('read') == 1
        assert await _phase(harness) == ChatPhase.IDLE
        harness.save_message.invoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_when_several_messages_in_preparing_expect_single_timer_and_last_read(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        await harness.user_message(message_id = 2)
        await harness.user_message(message_id = 3)

        assert len(harness.queue.payload_list) == 1  # таймер не сбрасывается
        await harness.run_all()

        assert harness.bot.action_list[0] == ('read', 3)
        assert harness.bot.sent_text_list == ["ответ"]

    @pytest.mark.asyncio
    async def test_when_read_fails_expect_answer_still_sent(
        self,
        harness: ChatStepHarness,
    ):
        harness.bot.read_error = RuntimeError("deleted")
        await harness.user_message(message_id = 1)

        await harness.run_all()

        assert harness.bot.sent_text_list == ["ответ"]

    @pytest.mark.asyncio
    async def test_when_remind_expect_answer_without_read_and_with_remind_flag(
        self,
        harness: ChatStepHarness,
    ):
        await harness.process_event.invoke(
            chat_id = CHAT_ID,
            event = ChatEvent(kind = ChatEventKind.REMIND),
            context = make_context(message_id = None, remind = True),
        )

        await harness.run_all()

        assert [p.kind for p in harness.queue.payload_list] == [ChatStepKind.GENERATE_AND_SEND]
        assert harness.bot.count('read') == 0
        assert harness.scenario.invoke.call_args.kwargs['remind'] is True
        assert harness.bot.sent_text_list == ["ответ"]
        assert await _phase(harness) == ChatPhase.IDLE


class TestStaleTicket:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("steps_before", [0, 1, 2])
    async def test_when_owner_replied_expect_every_step_ends_silently(
        self,
        harness: ChatStepHarness,
        steps_before: int,
    ):
        await harness.user_message(message_id = 1)
        for _ in range(steps_before):
            await harness.run_next()
        actions_before = list(harness.bot.action_list)

        await harness.owner_message()
        await harness.run_all()

        assert harness.bot.action_list == actions_before
        assert harness.bot.sent_text_list == []
        harness.scenario.invoke.assert_not_awaited()
        assert await _phase(harness) == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_owner_replied_during_sending_expect_remaining_dropped(
        self,
        harness: ChatStepHarness,
    ):
        harness.answer_list = ["первое", "второе", "третье"]
        harness.bot.after_send = harness.owner_message
        await harness.user_message(message_id = 1)

        await harness.run_all()

        assert harness.bot.sent_text_list == ["первое"]
        assert await _phase(harness) == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_new_message_during_answering_expect_single_answer_for_both(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        await harness.run_next()  # read
        await harness.run_next()  # typing; generate уже в очереди со старым талоном
        assert await _phase(harness) == ChatPhase.ANSWERING

        await harness.user_message(message_id = 2)
        await harness.run_all()

        # Старый generate устарел и не вызвал модель; новый ответ один
        assert harness.scenario.invoke.await_count == 1
        assert harness.bot.sent_text_list == ["ответ"]
        assert harness.bot.action_list.count(('read', 2)) == 1
        assert await _phase(harness) == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_new_message_during_generation_expect_old_answer_not_sent(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        await harness.run_next()
        await harness.run_next()
        old_generate = harness.queue.payload_list[2]

        async def new_message_while_generating(**kwargs) -> list[str]:
            await harness.user_message(message_id = 2)
            return ["старый ответ"]

        harness.scenario.invoke.side_effect = new_message_while_generating
        await harness.handle_step.invoke(payload = old_generate)
        harness.scenario.invoke.side_effect = harness._generate
        await harness.run_all()

        assert harness.bot.sent_text_list == ["ответ"]


class TestRedelivery:

    @pytest.mark.asyncio
    async def test_when_generate_delivered_twice_expect_single_answer(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        await harness.run_all()
        generate = harness.queue.payload_list[2]

        await harness.handle_step.invoke(payload = generate)

        assert harness.bot.sent_text_list == ["ответ"]

    @pytest.mark.asyncio
    async def test_when_read_delivered_twice_expect_next_step_scheduled_once(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        read = harness.queue.payload_list[0]

        await harness.handle_step.invoke(payload = read)
        await harness.handle_step.invoke(payload = read)

        assert [p.kind for p in harness.queue.payload_list] == [
            ChatStepKind.READ_MESSAGE,
            ChatStepKind.START_TYPING,
        ]
        assert harness.bot.count('read') == 1

    @pytest.mark.asyncio
    async def test_when_same_step_delivered_concurrently_expect_single_answer(
        self,
        harness: ChatStepHarness,
    ):
        await harness.user_message(message_id = 1)
        await harness.run_next()
        await harness.run_next()
        generate = harness.queue.payload_list[2]

        await asyncio.gather(
            harness.handle_step.invoke(payload = generate),
            harness.handle_step.invoke(payload = generate),
        )

        assert harness.bot.sent_text_list == ["ответ"]
        assert harness.scenario.invoke.await_count == 1


class TestTypingLifecycle:

    @pytest.mark.asyncio
    async def test_when_generation_fails_expect_typing_stopped_and_chat_idle(
        self,
        harness: ChatStepHarness,
    ):
        async def fail_after_pause(**kwargs) -> list[str]:
            await asyncio.sleep(0.05)
            raise RuntimeError("llm down")

        harness.scenario.invoke.side_effect = fail_after_pause
        await harness.user_message(message_id = 1)
        await harness.run_next()
        await harness.run_next()

        await harness.run_next()  # generate падает, но шаг не бросает

        typing_count = harness.bot.count('typing')
        await asyncio.sleep(0.05)
        assert harness.bot.count('typing') == typing_count
        assert harness.bot.sent_text_list == []
        assert await _phase(harness) == ChatPhase.IDLE
        other_tasks = asyncio.all_tasks() - {asyncio.current_task()}
        assert not other_tasks  # typing-задача не осталась висеть

    @pytest.mark.asyncio
    async def test_when_step_cancelled_expect_typing_stopped(
        self,
        harness: ChatStepHarness,
    ):
        started = asyncio.Event()

        async def hang(**kwargs) -> list[str]:
            started.set()
            await asyncio.sleep(60)
            return []

        harness.scenario.invoke.side_effect = hang
        await harness.user_message(message_id = 1)
        await harness.run_next()
        await harness.run_next()
        step = asyncio.create_task(harness.run_next())
        await started.wait()

        step.cancel()
        with pytest.raises(asyncio.CancelledError):
            await step

        other_tasks = asyncio.all_tasks() - {asyncio.current_task()}
        assert not other_tasks
