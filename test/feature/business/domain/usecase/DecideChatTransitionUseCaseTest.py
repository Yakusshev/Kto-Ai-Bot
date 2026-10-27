from datetime import datetime, timedelta, timezone

import pytest

from bot.feature.business.domain.model.ChatDecision import ChatAction
from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatState import ChatPhase, ChatState
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase

CHAT_ID = 1
NOW = datetime(2026, 1, 1, tzinfo = timezone.utc)


def _state(
    phase: ChatPhase = ChatPhase.IDLE,
    version: int = 0,
    phase_version: int = 0,
    pending: tuple[int, ...] = (),
) -> ChatState:
    return ChatState(
        chat_id = CHAT_ID,
        phase = phase,
        version = version,
        phase_version = phase_version,
        pending_message_ids = pending,
        updated_at = NOW,
    )


def _message(message_id: int) -> ChatEvent:
    return ChatEvent(kind = ChatEventKind.USER_MESSAGE, message_id = message_id)


class TestDecideChatTransitionUseCase:

    @pytest.fixture
    def use_case(self) -> DecideChatTransitionUseCase:
        return DecideChatTransitionUseCase()

    def test_when_idle_and_message_expect_preparing_and_start_timer(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        decision = use_case.invoke(_state(), _message(10), NOW)

        assert decision.action == ChatAction.START_PREPARING
        assert decision.state.phase == ChatPhase.PREPARING
        assert decision.state.version == 1
        assert decision.state.phase_version == 1
        assert decision.state.pending_message_ids == (10,)

    def test_when_preparing_and_message_expect_timer_not_reset(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        state = _state(ChatPhase.PREPARING, version = 1, phase_version = 1, pending = (10,))

        decision = use_case.invoke(state, _message(11), NOW)

        assert decision.action == ChatAction.NONE
        assert decision.state.phase == ChatPhase.PREPARING
        assert decision.state.version == 2
        assert decision.state.phase_version == 1  # талон таймера всё ещё актуален
        assert decision.state.pending_message_ids == (10, 11)
        assert decision.state.is_actual(state.ticket())

    def test_when_answering_and_message_expect_cancel_and_answer_now(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        state = _state(ChatPhase.ANSWERING, version=3, phase_version=3, pending=(10,))

        decision = use_case.invoke(state, _message(12), NOW)

        assert decision.action == ChatAction.CANCEL_AND_ANSWER_NOW
        assert decision.state.phase == ChatPhase.ANSWERING
        assert decision.state.version == 4
        assert not decision.state.is_actual(state.ticket())  # старый ответ отменён

    @pytest.mark.parametrize(
        'phase, expected_action',
        [
            (ChatPhase.IDLE, ChatAction.NONE),
            (ChatPhase.PREPARING, ChatAction.CANCEL),
            (ChatPhase.ANSWERING, ChatAction.CANCEL),
        ],
    )
    def test_when_owner_message_expect_idle_and_version_bumped(
        self,
        use_case: DecideChatTransitionUseCase,
        phase: ChatPhase,
        expected_action: ChatAction,
    ):
        state = _state(phase, version = 5, phase_version = 4, pending = (1,))

        decision = use_case.invoke(
            state,
            ChatEvent(kind = ChatEventKind.OWNER_MESSAGE, message_id = 99),
            NOW,
        )

        assert decision.action == expected_action
        assert decision.state.phase == ChatPhase.IDLE
        assert decision.state.version == 6
        assert decision.state.pending_message_ids == ()
        assert not decision.state.is_actual(state.ticket())

    def test_when_preparing_finished_with_actual_ticket_expect_answering(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        state = _state(ChatPhase.PREPARING, version = 2, phase_version = 1, pending = (1, 2))
        ticket = state.ticket()
        event = ChatEvent(kind = ChatEventKind.PREPARING_FINISHED, ticket = ticket)

        decision = use_case.invoke(state, event, NOW)

        assert decision.action == ChatAction.START_ANSWER
        assert decision.state.phase == ChatPhase.ANSWERING
        assert decision.state.version == 3
        assert decision.state.pending_message_ids == (1, 2)
        # Повторный/дублирующий шаг с тем же талоном уже устарел
        assert not decision.state.is_actual(ticket)

    def test_when_preparing_finished_after_owner_reply_expect_stale(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        old_ticket = _state(ChatPhase.PREPARING, version = 1, phase_version = 1).ticket()
        state = _state(ChatPhase.IDLE, version = 2, phase_version = 2)

        decision = use_case.invoke(
            state,
            ChatEvent(kind = ChatEventKind.PREPARING_FINISHED, ticket = old_ticket),
            NOW,
        )

        assert decision.action == ChatAction.STALE
        assert decision.state == state

    def test_when_old_timer_fires_in_new_cycle_expect_stale(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        old_ticket = _state(ChatPhase.PREPARING, version = 1, phase_version = 1).ticket()
        state = _state(ChatPhase.PREPARING, version = 4, phase_version = 4)

        decision = use_case.invoke(
            state,
            ChatEvent(kind = ChatEventKind.PREPARING_FINISHED, ticket = old_ticket),
            NOW,
        )

        assert decision.action == ChatAction.STALE

    def test_when_answer_finished_with_actual_ticket_expect_idle(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        state = _state(ChatPhase.ANSWERING, version = 3, phase_version = 1, pending = (1,))

        decision = use_case.invoke(
            state,
            ChatEvent(kind = ChatEventKind.ANSWER_FINISHED, ticket = state.ticket()),
            NOW,
        )

        assert decision.state.phase == ChatPhase.IDLE
        assert decision.state.pending_message_ids == ()
        assert decision.state.version == 4

    def test_when_answer_finished_after_new_message_expect_stale(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        old_ticket = _state(ChatPhase.ANSWERING, version = 3, phase_version = 3).ticket()
        state = _state(ChatPhase.ANSWERING, version = 4, phase_version = 4)

        decision = use_case.invoke(
            state,
            ChatEvent(kind = ChatEventKind.ANSWER_FINISHED, ticket = old_ticket),
            NOW,
        )

        assert decision.action == ChatAction.STALE
        assert decision.state == state

    def test_when_remind_in_idle_expect_answering(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        decision = use_case.invoke(_state(), ChatEvent(kind = ChatEventKind.REMIND), NOW)

        assert decision.action == ChatAction.START_ANSWER
        assert decision.state.phase == ChatPhase.ANSWERING
        assert decision.state.version == 1

    def test_when_remind_in_active_chat_expect_ignored(
        self,
        use_case: DecideChatTransitionUseCase,
    ):
        state = _state(ChatPhase.PREPARING, version = 1, phase_version = 1)

        decision = use_case.invoke(state, ChatEvent(kind = ChatEventKind.REMIND), NOW)

        assert decision.action == ChatAction.STALE
        assert decision.state == state

class TestStuckPhase:

    LATER = NOW + timedelta(minutes = 11)

    @pytest.mark.parametrize("phase", [ChatPhase.PREPARING, ChatPhase.ANSWERING])
    def test_when_message_in_stuck_phase_expect_new_preparing(
        self,
        phase: ChatPhase,
    ):
        state = _state(phase, version = 4, phase_version = 2, pending = (1,))

        decision = DecideChatTransitionUseCase().invoke(state, _message(9), self.LATER)

        assert decision.action == ChatAction.START_PREPARING
        assert decision.state.phase == ChatPhase.PREPARING
        assert decision.state.phase_version == 5
        assert decision.state.pending_message_ids == (9,)

    def test_when_remind_in_stuck_phase_expect_answering(self):
        state = _state(ChatPhase.PREPARING, version = 4, phase_version = 2)

        decision = DecideChatTransitionUseCase().invoke(
            state,
            ChatEvent(kind = ChatEventKind.REMIND),
            self.LATER,
        )

        assert decision.action == ChatAction.START_ANSWER

    def test_when_fresh_phase_expect_unchanged_behaviour(self):
        state = _state(ChatPhase.PREPARING, version = 4, phase_version = 2, pending = (1,))

        decision = DecideChatTransitionUseCase().invoke(state, _message(9), NOW + timedelta(minutes = 9))

        assert decision.action == ChatAction.NONE

