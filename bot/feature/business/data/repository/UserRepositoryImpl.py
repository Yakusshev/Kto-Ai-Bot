from typing import Tuple, List

from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.domain.model.UserModel import UserModel
from bot.feature.business.data.datasource.UserRemoteDataSource import \
    UserRemoteDataSource


class UserRepositoryImpl:

    def __init__(
        self,
        user_remote_data_source: UserRemoteDataSource,
        telegram_remote_data_source: TelegramRemoteDataSource,
    ):
        self._user_remote_data_source = user_remote_data_source
        self._telegram_remote_data_source = telegram_remote_data_source

    async def create_table(self) -> None:
        await self._user_remote_data_source.create_table_if_not_exists()

    async def add_users(
        self,
        user_model_list: List[UserModel],
    ) -> None:
        await self._user_remote_data_source.create_table_if_not_exists()
        await self._user_remote_data_source.add_users(user_model_list)

    async def get_all_users(self) -> Tuple[UserModel, ...]:
        return await self._user_remote_data_source.get_user_tuple()

    async def add_user(
        self,
        user: UserModel,
    ) -> None:
        await self._user_remote_data_source.create_table_if_not_exists()
        await self._user_remote_data_source.add_users([user])

    async def get_user_model_force(
        self,
        chat_id: int,
    ) -> UserModel:
        return await self._telegram_remote_data_source\
            .get_user_model(chat_id = chat_id)
