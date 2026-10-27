from datetime import datetime, timezone
from typing import Awaitable, Callable

from bot.feature.business.domain.model.ChatState import ChatState
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository


class FakeChatStateRepository(ChatStateRepository):
    """In-memory реализация порта с той же семантикой compare-and-set, что и в YDB."""

    def __init__(self) -> None:
        self.states: dict[int, ChatState] = {}
        # Хук между чтением и записью: имитирует другой экземпляр контейнера
        self.before_compare_and_set: Callable[[], Awaitable[None]] | None = None

    async def get(
        self,
        chat_id: int,
    ) -> ChatState:
        return self.states.get(chat_id) or ChatState.initial(
            chat_id = chat_id,
            now = datetime.now(timezone.utc),
        )

    async def compare_and_set(
        self,
        expected_version: int,
        new_state: ChatState,
    ) -> bool:
        if self.before_compare_and_set is not None:
            hook, self.before_compare_and_set = self.before_compare_and_set, None
            await hook()

        stored = self.states.get(new_state.chat_id)
        if (stored.version if stored else 0) != expected_version:
            return False
        self.states[new_state.chat_id] = new_state
        return True
