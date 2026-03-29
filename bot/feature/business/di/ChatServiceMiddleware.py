from typing import Callable, Dict, Any, Awaitable

import ydb
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.di.DiConst import DiConst
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.data.datasource.UserRemoteDataSource import \
    UserRemoteDataSource
from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.feature.business.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.feature.business.di.llm_module import get_llm_repository
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.GetChatStrListUseCase import \
    GetChatInfoTupleUseCase
from bot.feature.business.domain.usecase.GetForwardOriginTextForAiUseCase import \
    GetForwardOriginTextForAiUseCase
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase
from bot.feature.business.domain.usecase.GetUserListUseCase import GetUserListUseCase
from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.usecase.SendAiRequestUseCase import \
    SendAiRequestUseCase
from bot.feature.business.domain.usecase.UpdateUserTableFromChatHistoryUseCase import \
    UpdateUserTableFromChatHistoryUseCase
from bot.feature.business.entrypoint.service.ChatService import ChatService


class ChatServiceMiddleware(BaseMiddleware):

    def __init__(
        self,
        driver: ydb.Driver,
        ydb_session_pool: ydb.SessionPool,
    ):
        self.driver = driver
        self.ydb_session_pool = ydb_session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        data[DiConst.YDB_SESSION_POOL] = self.ydb_session_pool
        data[DiConst.YDB_DRIVER] = self.driver

        chat_history_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = self.ydb_session_pool,
            driver = self.driver,
        )

        data[DiConst.CHAT_HISTORY_REPOSITORY] = chat_history_repository

        strings = data["strings"]

        data["chat_service"] = ChatService(
            generate_ai_response_scenario = GenerateAiResponseScenario(
                handle_ai_response_use_case = HandleAiResponseUseCase(),
                send_ai_request_use_case = SendAiRequestUseCase(
                    session_repository = chat_history_repository,
                    ai_repository = get_llm_repository(),
                    getForwardOriginUseCase = GetForwardOriginTextForAiUseCase(
                        strings = strings,
                    ),
                    strings = strings,
                ),
                get_system_instruction_use_case = GetSystemInstructionUseCase(
                    strings = strings,
                ),
            ),
            save_message_use_case = SaveMessageUseCase(
                chat_history_repository = chat_history_repository,
            ),
            strings = strings,
        )

        data["get_chat_info_tuple_use_case"] = GetChatInfoTupleUseCase(
            chat_history_repository = chat_history_repository,
        )

        user_remote_data_source = \
            UserRemoteDataSource(
                ydb_session_pool = self.ydb_session_pool,
                driver = self.driver,
            )

        user_repository_impl = \
            UserRepositoryImpl(
                user_remote_data_source = user_remote_data_source,
                telegram_remote_data_source = TelegramRemoteDataSource(),
            )

        data[DiConst.USER_REPOSITORY] = user_repository_impl

        data["update_user_table_from_chat_history_use_case"] = \
            UpdateUserTableFromChatHistoryUseCase(
                chat_history_repository = chat_history_repository,
                user_repository = user_repository_impl,
            )

        data["get_user_list_use_case"] = \
            GetUserListUseCase(
                user_repository = user_repository_impl,
                chat_history_repository = chat_history_repository,
            )

        return await handler(event, data)

