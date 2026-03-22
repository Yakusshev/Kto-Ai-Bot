from bot.feature.business import user_bot_manager
from bot.feature.business.data.datasource.UserModelMapper import to_user_model
from bot.feature.business.domain.model.UserModel import UserModel


class TelegramRemoteDataSource:

    def __init__(self):
        self.bot = user_bot_manager.bot

    async def get_user_model(
        self,
        chat_id: int,
    ) -> UserModel:
        chat = await self.bot.get_chat(chat_id = chat_id)

        return to_user_model(chat = chat)