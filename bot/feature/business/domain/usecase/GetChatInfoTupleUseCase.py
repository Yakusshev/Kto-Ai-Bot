from typing import Tuple

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.domain.model.ChatInfoModel import ChatInfoModel
from bot.util.log_util import get_logger


class GetChatInfoTupleUseCase:

    def __init__(
        self,
        chat_history_repository: ChatHistoryRepositoryImpl,
    ):
        self.chat_history_repository = chat_history_repository

    async def invoke(self) -> str:

        chat_info_tuple = await self.chat_history_repository.get_chat_info_tuple()

        _logger.debug(f"invoke: {chat_info_tuple}")

        result = f"total users = {len(chat_info_tuple)}\n\n"
        for chat_info in chat_info_tuple:
            result += f"message_count = {chat_info.message_count}\n"
            result += f"    last_message_date = {chat_info.last_message_date}\n"
            result += f"    last_message_role = {chat_info.last_message_role}\n"
            result += f"    last_message_content = {chat_info.last_message_content}\n"
            result += f"    id = {chat_info.id}\n\n"

        return result

_logger = get_logger(GetChatInfoTupleUseCase.__name__)