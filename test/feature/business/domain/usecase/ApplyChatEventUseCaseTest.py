import pytest

from bot.feature.business.domain.model.ChatDecision import ChatAction
from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatState import ChatPhase
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import (
    ApplyChatEventUseCase,
    ChatStateConflictError,
)
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase
from bot.feature.business.domain.usecase.IsChatStepActualUseCase import \
    IsChatStepActualUseCase
from ..fake.FakeChatStateRepository import FakeChatStateRepository

CHAT_ID = 7


def _message(message_id: int) -> ChatEvent:
    return ChatEvent(kind = ChatEventKind.USER_MESSAGE, message_id = message_id)


class TestApplyChatEventUseCase:

    @pytest.fixture
    def repository(self) -> FakeChatStateRepository:
        return FakeChatStateRepository()

    @pytest.fixture
    def use_case(self, repository: FakeChatStateRepository) -> ApplyChatEventUseCase:
        return ApplyChatEventUseCase(
            chat_state_repository = repository,
            decide_chat_transition_use_case = DecideChatTransitionUseCase(),
        )

    @pytest.mark.asyncio
    async def test_when_message_expect_state_saved(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        decision = await use_case.invoke(CHAT_ID, _message(1))

        assert decision.action == ChatAction.START_PREPARING
        assert repository.states[CHAT_ID].phase == ChatPhase.PREPARING

    @pytest.mark.asyncio
    async def test_when_concurrent_write_expect_retry_on_fresh_state(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        # Между чтением и записью «другой экземпляр» успел принять сообщение 1
        async def other_instance():
            await repository.compare_and_set(
                expected_version = 0,
                new_state = DecideChatTransitionUseCase().invoke(
                    state = await repository.get(CHAT_ID),
                    event = _message(1),
                    now = (await repository.get(CHAT_ID)).updated_at,
                ).state,
            )

        repository.before_compare_and_set = other_instance

        decision = await use_case.invoke(CHAT_ID, _message(2))

        # Наше сообщение пересчитано по свежему состоянию: preparing + msg, таймер один
        assert decision.action == ChatAction.NONE
        state = repository.states[CHAT_ID]
        assert state.version == 2
        assert state.pending_message_ids == (1, 2)

    @pytest.mark.asyncio
    async def test_when_two_messages_in_a_row_expect_single_timer_and_both_saved(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        first = await use_case.invoke(CHAT_ID, _message(1))
        second = await use_case.invoke(CHAT_ID, _message(2))

        assert first.action == ChatAction.START_PREPARING
        assert second.action == ChatAction.NONE
        assert repository.states[CHAT_ID].version == 2
        assert repository.states[CHAT_ID].pending_message_ids == (1, 2)

    @pytest.mark.asyncio
    async def test_when_message_during_answering_expect_old_step_stale(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        is_actual = IsChatStepActualUseCase(chat_state_repository = repository)
        first = await use_case.invoke(CHAT_ID, _message(1))
        answering = await use_case.invoke(
            CHAT_ID,
            ChatEvent(kind = ChatEventKind.PREPARING_FINISHED, ticket = first.state.ticket()),
        )
        answer_ticket = answering.state.ticket()
        assert await is_actual.invoke(answer_ticket)

        cancel = await use_case.invoke(CHAT_ID, _message(2))

        assert cancel.action == ChatAction.CANCEL_AND_ANSWER_NOW
        assert not await is_actual.invoke(answer_ticket)
        assert await is_actual.invoke(cancel.state.ticket())

    @pytest.mark.asyncio
    async def test_when_stale_step_expect_state_not_changed(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        first = await use_case.invoke(CHAT_ID, _message(1))
        await use_case.invoke(
            CHAT_ID,
            ChatEvent(kind = ChatEventKind.OWNER_MESSAGE, message_id = 5),
        )
        before = repository.states[CHAT_ID]

        decision = await use_case.invoke(
            CHAT_ID,
            ChatEvent(kind = ChatEventKind.PREPARING_FINISHED, ticket = first.state.ticket()),
        )

        assert decision.action == ChatAction.STALE
        assert repository.states[CHAT_ID] == before

    @pytest.mark.asyncio
    async def test_when_conflicts_never_end_expect_error(
        self,
        use_case: ApplyChatEventUseCase,
        repository: FakeChatStateRepository,
    ):
        async def always_false(expected_version, new_state):
            return False

        repository.compare_and_set = always_false  # type: ignore[method-assign]

        with pytest.raises(ChatStateConflictError):
            await use_case.invoke(CHAT_ID, _message(1))
