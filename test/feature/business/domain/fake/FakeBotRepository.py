from typing import Awaitable, Callable

from bot.feature.business.domain.model.SaveMessageModel import (
    MessageRole,
    OwnerModel,
    SaveMessageModel,
)
from bot.feature.business.domain.repository.BotRepository import BotRepository
from datetime import datetime, timezone


class FakeBotRepository(BotRepository):
    """Записывает действия бота в Telegram в порядке вызова."""

    def __init__(self) -> None:
        self.action_list: list[tuple[str, int | str | None]] = []
        self.read_error: Exception | None = None
        # Хук после отправки сообщения: имитирует событие посреди ответа
        self.after_send: Callable[[], Awaitable[None]] | None = None

    @property
    def sent_text_list(self) -> list[str]:
        return [str(value) for name, value in self.action_list if name == 'send']

    def count(
        self,
        name: str,
    ) -> int:
        return len([action for action, _ in self.action_list if action == name])

    async def read_message(
        self,
        chat_id: int,
        business_connection_id: str,
        message_id: int,
    ) -> None:
        if self.read_error is not None:
            raise self.read_error
        self.action_list.append(('read', message_id))

    async def send_typing_chat_action(
        self,
        chat_id: int,
        business_connection_id: str,
    ) -> None:
        self.action_list.append(('typing', None))

    async def send_message(
        self,
        chat_id: int,
        business_connection_id: str,
        text: str,
    ) -> SaveMessageModel | None:
        self.action_list.append(('send', text))
        if self.after_send is not None:
            await self.after_send()
        return SaveMessageModel(
            chat_id = chat_id,
            created_at = datetime(2026, 1, 1, tzinfo = timezone.utc),
            message_id = 1000 + len(self.action_list),
            role = MessageRole.ASSISTANT,
            content = text,
            event_type = 'text',
            reply_to_id = None,
            text_quote = None,
            business_connection_id = business_connection_id,
            forward_origin = None,
        )

    async def get_business_connection_owner(
        self,
        id: str,
    ) -> OwnerModel:
        return OwnerModel(id = 1, username = 'owner', full_name = 'Owner')
