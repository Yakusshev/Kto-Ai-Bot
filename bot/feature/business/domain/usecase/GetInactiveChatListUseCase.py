from datetime import datetime

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.feature.business.domain.model.InactiveChatModel import InactiveChatModel
from bot.feature.business.domain.model.UserModel import UserModel
from bot.util.log_util import get_logger


class GetInactiveChatListUseCase:

    def __init__(
        self,
        chat_history_repository: ChatHistoryRepositoryImpl,
        user_repository: UserRepositoryImpl,
    ):
        self.chat_history_repository = chat_history_repository
        self._user_repository = user_repository

    async def invoke(self) -> list[InactiveChatModel]:

        user_tuple = await self._user_repository.get_all_users()
        chat_info_tuple = await self.chat_history_repository.get_chat_info_tuple()

        users_dict: dict[int, UserModel] = {user.id: user for user in user_tuple}

        result_list: list[InactiveChatModel] = []
        for chat_info_model in chat_info_tuple:

            now = datetime.now()  # Текущее время
            diff = now - chat_info_model.last_message_date
            diff_in_hours = diff.total_seconds() / 3600

            if 16 < diff_in_hours < 48:
                user = users_dict.get(chat_info_model.id)
                if user:
                    result_list.append(
                        InactiveChatModel(
                            user_model = user,
                            chat_info_model = chat_info_model,
                        )
                    )

        _logger.debug(f"invoke: {result_list}")

        return result_list

_logger = get_logger(GetInactiveChatListUseCase.__name__)