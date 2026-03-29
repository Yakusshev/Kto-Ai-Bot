import ydb
from aiogram_i18n import I18nMiddleware
from ydb.aio import Driver

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
from bot.resource.GracefulShutdownFluentRuntimeCore import \
    GracefulShutdownFluentRuntimeCore
from bot.resource.Strings import Strings


class ReminderServiceProvider:

    @staticmethod
    def create(
        ydb_session_pool: ydb.SessionPool,
        driver: Driver,
    ) -> ReminderService:
        i18n = I18nMiddleware(
            core = GracefulShutdownFluentRuntimeCore(
                path = "bot/resource/locales/{locale}",
            ),
            default_locale = "ru",
        )

        i18n = i18n.new_context(
            locale = "ru",
            data = {},
        )

        strings = Strings(i18n = i18n)

        chat_history_repository = ChatHistoryRepositoryImpl(
            ydb_session_pool = ydb_session_pool,
            driver = driver,
        )

        user_repository_impl = UserRepositoryImpl(
            user_remote_data_source = UserRemoteDataSource(
                ydb_session_pool = ydb_session_pool,
                driver = driver,
            ),
            telegram_remote_data_source = TelegramRemoteDataSource(),
        )

        return ReminderService(
            generate_ai_response_scenario = GenerateAiResponseScenario(
                handle_ai_response_use_case = HandleAiResponseUseCase(),
                send_ai_request_use_case = SendAiRequestUseCase(
                    session_repository = ChatHistoryRepositoryImpl(
                        ydb_session_pool = ydb_session_pool,
                        driver = driver,
                    ),
                    ai_repository = get_llm_repository(),
                    getForwardOriginUseCase = GetForwardOriginTextForAiUseCase(
                        strings = strings,
                    ),
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