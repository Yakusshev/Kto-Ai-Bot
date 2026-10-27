from datetime import datetime, timezone

from bot.feature.business.data.datasource.ChatStateRemoteDataSource import \
    ChatStateRemoteDataSource
from bot.feature.business.domain.model.ChatState import ChatState
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository


class ChatStateRepositoryImpl(ChatStateRepository):
    """Состояние диалога в YDB: общее для всех экземпляров контейнера."""

    def __init__(
        self,
        chat_state_remote_data_source: ChatStateRemoteDataSource,
    ):
        self._remote = chat_state_remote_data_source

    async def get(
        self,
        chat_id: int,
    ) -> ChatState:
        state = await self._remote.get(chat_id = chat_id)
        return state or ChatState.initial(
            chat_id = chat_id,
            now = datetime.now(timezone.utc),
        )

    async def compare_and_set(
        self,
        expected_version: int,
        new_state: ChatState,
    ) -> bool:
        return await self._remote.compare_and_set(
            expected_version = expected_version,
            new_state = new_state,
        )
