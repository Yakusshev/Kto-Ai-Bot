from bot.feature.business import user_bot_manager
from bot.feature.business.data.datasource.UserModelMapper import to_user_model
from bot.feature.business.domain.model.SaveMessageModel import OwnerModel
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

    async def send_message(
        self,
        chat_id: int,
        business_connection_id: str,
        text: str,
    ):
        self.bot.send_message(
            chat_id = chat_id,
            business_connection_id = business_connection_id,
            text = text,
        )

    async def get_business_connection_owner(
        self,
        id: str,
    ) -> OwnerModel:
        connection = await self.bot\
            .get_business_connection(business_connection_id = id)

        return OwnerModel(
            id = connection.user.id,
            username = connection.user.username,
            full_name = connection.user.full_name,
        )


