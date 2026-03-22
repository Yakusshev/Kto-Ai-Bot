import asyncio
import traceback

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.feature.business.domain.model.UserModel import UserModel
from bot.util.log_util import get_logger


class UpdateUserTableFromChatHistoryUseCase:

    def __init__(
        self,
        chat_history_repository: ChatHistoryRepositoryImpl,
        user_repository: UserRepositoryImpl,
    ):
        self.chat_history_repository = chat_history_repository
        self.user_repository = user_repository

    async def invoke(self):

        chat_info_tuple = await self.chat_history_repository.get_chat_info_tuple()

        _logger.debug(f"invoke: {chat_info_tuple}")

        task_list = [
            self.user_repository\
                .get_user_model_force(chat_id = chat.id) for chat in chat_info_tuple
        ]

        results: list[UserModel] = []

        # Обрабатывает результаты по мере завершения
        for coro in asyncio.as_completed(task_list):
            try:
                user_model = await coro
                results.append(user_model)
                _logger.debug(f"Получен пользователь: {user_model}")
            except Exception as e:
                if str(e) == "Telegram server says - Bad Request: chat not found":
                    _logger.error(e)
                else:
                    _logger.error(f"Ошибка получения пользователя {traceback.format_exception(e)}")


        _logger.debug(f"Завершение загрузки информации и пользователях")

        await self.user_repository.add_users(user_model_list = results)

_logger = get_logger(UpdateUserTableFromChatHistoryUseCase.__name__)