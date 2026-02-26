from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from ydb import SessionPool

from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.di.llm_module import get_llm_repository
from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.entrypoint.ChatService import ChatService

class ChatServiceMiddleware(BaseMiddleware):

    def __init__(
        self,
        ydb_session_pool: SessionPool,
    ):
        self.ydb_session_pool = ydb_session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        session_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = self.ydb_session_pool,
        )

        data["chat_service"] = ChatService(
            generate_ai_response_use_case = GenerateAiResponseUseCase(
                session_repository = session_repository,
                llm_repository = get_llm_repository(),
            ),
            save_message_use_case = SaveMessageUseCase(
                session_repository = session_repository,
            ),
        )

        return await handler(event, data)