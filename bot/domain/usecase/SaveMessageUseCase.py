from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.domain.model.SaveMessageModel import SaveMessageModel


class SaveMessageUseCase:

    def __init__(
        self,
        session_repository: ChatHistoryRepositoryImpl,
    ):
        self.session_repository = session_repository

    async def invoke(
        self,
        save_message_model_list: list[SaveMessageModel],
    ):
        await self.session_repository.add_text_message_list(
            message_list = save_message_model_list,
        )
