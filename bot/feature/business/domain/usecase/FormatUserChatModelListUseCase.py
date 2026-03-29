from typing import Any

from bot.feature.business.domain.model.UserChatModel import UserChatModel


class FormatUserChatModelListUseCase:

    def invoke(
        self,
        user_list: list[UserChatModel],
    ) -> list[str]:

        result_list: list[str] = []

        result = f"total users = {len(user_list)}\n\n"

        for user_chat in user_list:
            user = user_chat.user_model
            if user:
                result += f"@{user.username}\n"
                result += f"first_name + last_name = [{user.first_name}][{user.last_name}]\n"
                result = self.add(body = result, data = user.bio, title = "bio")
                result = self.add(body = result, data = user.birthdate, title = "birthdate")

                update_date = user.update_date.strftime("%Y-%m-%d %A %H:%M")
                result = self.add(body = result, data = update_date, title = "update_date")
                result += f"channel @{user.channel_username}; {user.channel_title}\n"
            else:
                result += f"user не найден\n"

            chat = user_chat.chat_info_model
            result += f"message_count = {chat.message_count}\n"
            update_date = chat.last_message_date.strftime("%Y-%m-%d %A %H:%M")
            result += f"last_message: {update_date}\n"
            result += f"    {chat.last_message_role}\n"
            result += f"    {chat.last_message_content}\n"
            result += f"/remind {chat.id}\n"
            result += "\n"

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

