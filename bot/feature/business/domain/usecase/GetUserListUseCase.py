from typing import Any

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.domain.model.UserModel import UserModel
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.util.log_util import get_logger


class GetUserListUseCase:

    def __init__(
        self,
        user_repository: UserRepositoryImpl,
        chat_history_repository: ChatHistoryRepositoryImpl,
    ):
        self._user_repository = user_repository
        self.chat_history_repository = chat_history_repository

    async def invoke(self) -> list[str]:

        user_tuple = await self._user_repository.get_all_users()
        chat_info_tuple = await self.chat_history_repository.get_chat_info_tuple()

        users_dict: dict[int, UserModel] = {user.id: user for user in user_tuple}

        _logger.debug(f"invoke: {chat_info_tuple}")

        result_list = []

        result = f"total users = {len(chat_info_tuple)}\n\n"

        for chat_info in chat_info_tuple:
            user = users_dict.get(chat_info.id)

            if user:
                result += f"username = @{user.username}\n"
                result += f"first_name + last_name = [{user.first_name}][{user.last_name}]\n"
                result = self.add(body = result, data = user.bio, title = "bio")
                result = self.add(body = result, data = user.birthdate, title = "birthdate")
                result = self.add(body = result, data = user.update_date, title = "update_date")
                result += f"channel_username = @{user.channel_username}\n"
                result = self.add(body = result, data = user.channel_title, title = "channel_title")
                result = self.add(body = result, data = user.channel_id, title = "channel_id")
            else:
                result += f"user не найден\n"


            result += f"message_count = {chat_info.message_count}\n"
            result += f"    last_message_date = {chat_info.last_message_date}\n"
            result += f"    last_message_role = {chat_info.last_message_role}\n"
            result += f"    last_message_content = {chat_info.last_message_content}\n"
            result += f"    id = {chat_info.id}\n\n"

            if len(result) > 3500:
                result_list.append(result)
                result = ""

        if result:
            result_list.append(result)

        return result_list

    @staticmethod
    def add(
        body: str,
        data: Any,
        title: str,
    ) -> str:
        if data:
            body += f"{title} = {data}\n"
        return body


_logger = get_logger(GetUserListUseCase.__name__)
