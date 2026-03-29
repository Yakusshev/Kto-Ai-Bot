from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.di.DiConst import DiConst
from bot.feature.business.data.datasource.LocalDataSource import LocalDataSource
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.data.datasource.UserRemoteDataSource import \
    UserRemoteDataSource
from bot.feature.business.data.repository.BotRepositoryImpl import BotRepositoryImpl
from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.feature.business.di.llm_module import get_llm_repository
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.GetForwardOriginTextForAiUseCase import \
    GetForwardOriginTextForAiUseCase
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase
from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.usecase.SendAiRequestUseCase import \
    SendAiRequestUseCase
from bot.feature.business.domain.usecase.TypingLoopUseCase import TypingLoopUseCase
from bot.feature.business.entrypoint.service.ReminderService import ReminderService
from bot.util.log_util import get_logger


class ReminderServiceMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        strings = data["strings"]

        chat_history_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = data[DiConst.YDB_SESSION_POOL],
            driver = data[DiConst.YDB_DRIVER],
        )

        user_repository_impl = UserRepositoryImpl(
            user_remote_data_source = UserRemoteDataSource(
                ydb_session_pool = data[DiConst.YDB_SESSION_POOL],
                driver = data[DiConst.YDB_DRIVER],
            ),
            telegram_remote_data_source = TelegramRemoteDataSource(),
        )

        data[DiConst.REMINDER_SERVICE] = ReminderService(
            generate_ai_response_scenario = GenerateAiResponseScenario(
                handle_ai_response_use_case = HandleAiResponseUseCase(),
                send_ai_request_use_case = SendAiRequestUseCase(
                    session_repository = ChatHistoryRepositoryImpl(
                        ydb_session_pool = data[DiConst.YDB_SESSION_POOL],
                        driver = data[DiConst.YDB_DRIVER],
                    ),
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
            get_inactive_chat_list_use_case = GetInactiveChatListUseCase(
                chat_history_repository = chat_history_repository,
                user_repository = user_repository_impl,
            ),
            bot_repository = BotRepositoryImpl(
                telegram_remote_data_source = TelegramRemoteDataSource(),
                local_data_source = LocalDataSource(),
            ),
            task_scheduler = TaskSchedulerRepositoryImpl(),
            typing_loop_use_case = TypingLoopUseCase(
                bot_repository = BotRepositoryImpl(
                    telegram_remote_data_source = TelegramRemoteDataSource(),
                    local_data_source = LocalDataSource(),
                ),
            ),
            save_message_use_case = SaveMessageUseCase(
                chat_history_repository = chat_history_repository,
            ),
        )

        return await handler(event, data)


logger = get_logger(ReminderServiceMiddleware.__name__)