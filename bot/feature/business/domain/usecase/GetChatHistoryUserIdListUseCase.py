from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.util.log_util import get_logger


class GetChatHistoryUserIdListUseCase:

    def __init__(
        self,
        chat_history_repository: ChatHistoryRepositoryImpl,
    ):
        self.chat_history_repository = chat_history_repository

    async def invoke(self) -> list[int]:

        chat_info_tuple = await self.chat_history_repository.get_chat_info_tuple()

        _logger.debug(f"invoke: {chat_info_tuple}")

        id_list = [chat.id for chat in chat_info_tuple]

        return id_list

_logger = get_logger(GetChatHistoryUserIdListUseCase.__name__)