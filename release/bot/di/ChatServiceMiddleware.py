from typing import Callable, Dict, Any, Awaitable

import ydb
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from ydb import SessionPool

from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.di.llm_module import get_llm_repository
from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.entrypoint.ChatService import ChatService

class ChatServiceMiddleware(BaseMiddleware):

    def __init__(
        self,
    ):
        self.driver = create_ydb_driver()
        self.ydb_session_pool = ydb.SessionPool(self.driver)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        session_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = self.ydb_session_pool,
            driver = self.driver,
        )

        data["chat_service"] = ChatService(
            generate_ai_response_use_case = GenerateAiResponseUseCase(
                session_repository = session_repository,
                ai_repository = get_llm_repository(),
            ),
            save_message_use_case = SaveMessageUseCase(
                session_repository = session_repository,
            ),
            strings = data["strings"],
        )

        return await handler(event, data)