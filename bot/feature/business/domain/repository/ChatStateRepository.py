from abc import ABC, abstractmethod

from bot.feature.business.domain.model.ChatState import ChatState


class ChatStateRepository(ABC):
    """Хранилище состояния диалога по чатам (общее для всех экземпляров контейнера)."""

    @abstractmethod
    async def get(
        self,
        chat_id: int,
    ) -> ChatState:
        """Текущее состояние чата; для нового чата - IDLE с version = 0."""
        pass

    @abstractmethod
    async def compare_and_set(
        self,
        expected_version: int,
        new_state: ChatState,
    ) -> bool:
        """
        Атомарно (одна транзакция) записывает new_state, если сохранённая
        version равна expected_version (0 - строки ещё нет).
        False, если чат успел изменить другой экземпляр: состояние нужно перечитать.
        """
        pass
