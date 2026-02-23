from aiogram_i18n import I18nContext

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
        i18n: I18nContext,
    ):
        if not save_message_model.content:
            save_message_model.content = i18n.get('empty-message')

        await self.session_repository.add_text_message(
            message=save_message_model,
        )
