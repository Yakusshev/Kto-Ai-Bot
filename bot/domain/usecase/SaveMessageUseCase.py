from bot.data.repository.SessionRepository import SessionRepository
from bot.domain.model.SaveMessageModel import SaveMessageModel


class SaveMessageUseCase:

    def __init__(
        self,
        session_repository: SessionRepository,
    ):
        self.session_repository = session_repository

    async def invoke(
        self,
        save_message_model: SaveMessageModel,
    ):
        await self.session_repository.add_text_message(
            message = save_message_model,
        )
