from abc import abstractmethod, ABC

from bot.domain.model.PendingChat import PendingChat
from bot.domain.model.SaveMessageModel import SaveMessageModel


class DebounceRepository(ABC):

    @abstractmethod
    async def get_state(
        self,
        chat_id: int,
    ) -> PendingChat | None:
        pass

    @abstractmethod
    async def set_last_message_time(
        self,
        chat_id: int,
    ):
        pass

    @abstractmethod
    async def add_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
    ) -> SaveMessageModel:
        pass

    @abstractmethod
    async def pop_messages(
        self,
        chat_id: int,
    ) -> list[SaveMessageModel]:
        """Забрать и удалить все накопленные сообщения."""
        pass
