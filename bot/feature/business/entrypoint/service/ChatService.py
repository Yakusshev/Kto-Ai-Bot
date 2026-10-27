from aiogram.types import Message

from bot.feature.business.domain.model.SaveMessageModel import MessageRole
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.entrypoint.SaveMessageModelMapper import \
    to_save_message_model
from bot.resource.Strings import Strings
from bot.util.log_util import get_logger


class ChatService:

    def __init__(
        self,
        save_message_use_case: SaveMessageUseCase,
        strings: Strings,
    ):
        self.save_message_use_case = save_message_use_case
        self.strings = strings

    async def save_message(
        self,
        message: Message,
        text_content: str,
        role: MessageRole,
    ):
        save_message_model = to_save_message_model(
            message = message,
            content = text_content,
            role = role,
        )

        if save_message_model:
            await self.save_message_use_case.invoke(
                save_message_model_list = [save_message_model],
            )
        else:
            _logger.warning(
                f"save_message: пустой text_content, "
                f"role = {role}, message = {message}",
            )


_logger = get_logger(ChatService.__name__)
