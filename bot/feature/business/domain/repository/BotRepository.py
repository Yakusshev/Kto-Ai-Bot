from abc import ABC, abstractmethod

from bot.feature.business.domain.model.SaveMessageModel import OwnerModel, \
    SaveMessageModel


class BotRepository(ABC):
    """Действия бота в Telegram от имени владельца бизнес-аккаунта."""

    @abstractmethod
    async def read_message(
        self,
        chat_id: int,
        business_connection_id: str,
        message_id: int,
    ) -> None:
        """Помечает сообщение прочитанным."""
        pass

    @abstractmethod
    async def send_typing_chat_action(
        self,
        chat_id: int,
        business_connection_id: str,
    ) -> None:
        """Показывает собеседнику «печатает...»."""
        pass

    @abstractmethod
    async def send_message(
        self,
        chat_id: int,
        business_connection_id: str,
        text: str,
    ) -> SaveMessageModel | None:
        """Отправляет текст; возвращает запись об отправленном сообщении для истории."""
        pass

    @abstractmethod
    async def get_business_connection_owner(
        self,
        id: str,
    ) -> OwnerModel:
        """Владелец бизнес-аккаунта по id подключения."""
        pass
