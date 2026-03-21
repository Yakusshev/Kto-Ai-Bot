from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel
from bot.util.log_util import get_logger


class SaveMessageUseCase:

    def __init__(
        self,
        chat_history_repository: ChatHistoryRepositoryImpl,
    ):
        self.session_repository = chat_history_repository

    async def invoke(
        self,
        save_message_model_list: list[SaveMessageModel],
    ):
        _logger.debug(f"invoke = {save_message_model_list}")
        await self.session_repository.add_text_message_list(
            message_list = save_message_model_list,
        )

_logger = get_logger(SaveMessageUseCase.__name__)