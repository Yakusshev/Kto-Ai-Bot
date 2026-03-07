from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

import ydb
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.feature.business.di.llm_module import get_llm_repository
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.GetForwardOriginUseCase import \
    GetForwardOriginUseCase
from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase
from bot.feature.business.domain.usecase.SendAiRequestUseCase import \
    SendAiRequestUseCase
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.entrypoint.ChatService import ChatService


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
        data: Dict[str, Any],
    ) -> Any:
        session_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = self.ydb_session_pool,
            driver = self.driver,
        )

        strings = data["strings"]

        data["chat_service"] = ChatService(
            generate_ai_response_scenario = GenerateAiResponseScenario(
                handle_ai_response_use_case = HandleAiResponseUseCase(),
                send_ai_request_use_case = SendAiRequestUseCase(
                    session_repository = session_repository,
                    ai_repository = get_llm_repository(),
                    getForwardOriginUseCase = GetForwardOriginUseCase(
                        strings = strings,
                    ),
                ),
                get_system_instruction_use_case = GetSystemInstructionUseCase(
                    strings = strings,
                ),
            ),
            save_message_use_case = SaveMessageUseCase(
                session_repository = session_repository,
            ),
            strings = strings,
        )

        return await handler(event, data)
