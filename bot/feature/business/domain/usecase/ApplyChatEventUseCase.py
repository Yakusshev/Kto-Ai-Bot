from datetime import datetime, timezone

from bot.feature.business.domain.model.ChatDecision import ChatAction, ChatDecision
from bot.feature.business.domain.model.ChatEvent import ChatEvent
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase

MAX_ATTEMPTS = 10


class ChatStateConflictError(Exception):
    """Не удалось записать состояние чата: слишком много конкурирующих изменений."""


class ApplyChatEventUseCase:
    """
    Применяет событие к состоянию чата: читает, решает, пишет атомарно.
    При гонке экземпляров (version изменилась между чтением и записью)
    перечитывает состояние и повторяет решение уже по свежим данным.
    """

    def __init__(
        self,
        chat_state_repository: ChatStateRepository,
        decide_chat_transition_use_case: DecideChatTransitionUseCase,
    ):
        self._repository = chat_state_repository
        self._decide = decide_chat_transition_use_case

    async def invoke(
        self,
        chat_id: int,
        event: ChatEvent,
    ) -> ChatDecision:
        for _ in range(MAX_ATTEMPTS):
            state = await self._repository.get(chat_id = chat_id)
            decision = self._decide.invoke(
                state = state,
                event = event,
                now = datetime.now(timezone.utc),
            )

            if decision.action == ChatAction.STALE:
                return decision

            is_written = await self._repository.compare_and_set(
                expected_version = state.version,
                new_state = decision.state,
            )
            if is_written:
                return decision

        raise ChatStateConflictError(f"chat_id={chat_id}: конфликт записи состояния")
