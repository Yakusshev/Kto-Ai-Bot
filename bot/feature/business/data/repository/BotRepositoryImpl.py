from bot.feature.business.data.datasource.LocalDataSource import LocalDataSource
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource


class BotRepositoryImpl:

    def __init__(
        self,
        telegram_remote_data_source: TelegramRemoteDataSource,
        local_data_source: LocalDataSource,
    ):
        self._telegram_remote_data_source = telegram_remote_data_source
        self._local_data_source = local_data_source

    async def send_message(
        self,
        chat_id: int,
        business_connection_id: str,
        text: str,
    ):
        await self._telegram_remote_data_source.send_message(
            chat_id = chat_id,
            business_connection_id = business_connection_id,
            text = text,
        )

    async def get_business_connection_owner(
        self,
        id: str,
    ):
        owner = self._local_data_source.get_owner()

        if owner:
            return owner
        else:
            owner = await self._telegram_remote_data_source\
                .get_business_connection_owner(id = id)
            self._local_data_source.set_owner(owner = owner)
            return owner
