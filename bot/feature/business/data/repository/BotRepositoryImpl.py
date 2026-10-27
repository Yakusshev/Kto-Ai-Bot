from aiogram.types import Message

from bot.feature.business.data.datasource.LocalDataSource import LocalDataSource
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.domain.model.SaveMessageModel import (
    MessageRole,
    OwnerModel,
    SaveMessageModel,
)
from bot.feature.business.domain.repository.BotRepository import BotRepository


class BotRepositoryImpl(BotRepository):

    def __init__(
        self,
        telegram_remote_data_source: TelegramRemoteDataSource,
        local_data_source: LocalDataSource,
    ):
        self._telegram_remote_data_source = telegram_remote_data_source
        self._local_data_source = local_data_source

    async def read_message(
        self,
        chat_id: int,
        business_connection_id: str,
        message_id: int,
    ) -> None:
        await self._telegram_remote_data_source.read_business_message(
            chat_id = chat_id,
            business_connection_id = business_connection_id,
            message_id = message_id,
        )

    async def send_message(
        self,
        chat_id: int,
        business_connection_id: str,
        text: str,
    ) -> SaveMessageModel | None:
        sent = await self._telegram_remote_data_source.send_message(
            chat_id = chat_id,
            business_connection_id = business_connection_id,
            text = text,
        )
        return _to_sent_message_model(
            sent = sent,
            business_connection_id = business_connection_id,
        )

    async def get_business_connection_owner(
        self,
        id: str,
    ) -> OwnerModel:
        owner = self._local_data_source.get_owner()

        if owner:
            return owner
        else:
            owner = await self._telegram_remote_data_source\
                .get_business_connection_owner(id = id)
            self._local_data_source.set_owner(owner = owner)
            return owner

    async def send_typing_chat_action(
        self,
        chat_id: int,
        business_connection_id: str,
    ) -> None:
        await self._telegram_remote_data_source.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = business_connection_id,
        )


def _to_sent_message_model(
    sent: Message,
    business_connection_id: str,
) -> SaveMessageModel | None:
    """Запись об отправленном ботом тексте (ответов и цитат у него нет)."""
    if not sent.text:
        return None

    return SaveMessageModel(
        chat_id = sent.chat.id,
        created_at = sent.date,
        message_id = sent.message_id,
        role = MessageRole.ASSISTANT,
        content = sent.text,
        event_type = 'text',
        reply_to_id = None,
        text_quote = None,
        business_connection_id = business_connection_id,
        forward_origin = None,
    )
