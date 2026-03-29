# main.py
import asyncio
import locale
import logging

import ydb
from aiogram import Dispatcher, types
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.core.domain.const.env_const import DEBUG_MODE_START_POLLING
from bot.feature.admin import admin_bot_manager
from bot.feature.admin.di.ReminderServiceMiddleware import ReminderServiceMiddleware
from bot.feature.admin.entrypoint.handler.admin_handlers import admin_router
from bot.feature.business import user_bot_manager
from bot.feature.business.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.feature.business.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.feature.business.di.ReminderServiceProvider import ReminderServiceProvider
from bot.feature.business.di.StringsMiddleware import StringsMiddleware
from bot.feature.business.entrypoint.business_message_handlers import business_router
from bot.resource.GracefulShutdownFluentRuntimeCore import \
    GracefulShutdownFluentRuntimeCore
from bot.util.log_util import get_logging_config
import logging.config
from bot.feature.admin.di.GetRemindInfoTextScenarioMiddleware import \
    GetRemindInfoTextScenarioMiddleware


async def main():
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    driver = create_ydb_driver()
    ydb_session_pool = ydb.SessionPool(driver)

    chat_service_middleware = ChatServiceMiddleware(
        driver = driver,
        ydb_session_pool = ydb_session_pool,
    )

    await start_admin_bot(chat_service_middleware)
    await prepare_business_bot(chat_service_middleware)

    loop = asyncio.get_event_loop()
    while True:
        user_input = await loop \
            .run_in_executor(None, input, "Ожидание ввода команды\n")
        if user_input.lower() == "exit":
            print("exit command received")
            break
        else:
            print("unknown command")


async def prepare_business_bot(
    chat_service_middleware: ChatServiceMiddleware,
):
    i18n = I18nMiddleware(
        core = GracefulShutdownFluentRuntimeCore(
            path = "bot/resource/locales/{locale}",
        ),
        default_locale = "ru",
    )
    i18n.setup(dispatcher = user_bot_manager.dispatcher)

    user_bot_manager.dispatcher.business_message.middleware(StringsMiddleware())

    user_bot_manager.dispatcher.business_message.middleware(chat_service_middleware)

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @user_bot_manager.dispatcher.business_connection()
    async def on_business_connection(connection: types.BusinessConnection):
        """Логирует факт подключения или отключения."""
        conn_id = connection.id
        is_enabled = connection.is_enabled
        user_id = connection.user.id

        if is_enabled:
            logging.info(
                f"User {user_id} connected business account. Connection ID: {conn_id}",
            )
        else:
            logging.warning(
                f"User {user_id} DISABLED business account. Connection ID: {conn_id}",
            )

    user_bot_manager.dispatcher.include_router(router = business_router)

    if DEBUG_MODE_START_POLLING:
        await user_bot_manager.start()


async def start_admin_bot(
    chat_service_middleware: ChatServiceMiddleware,
):
    I18nMiddleware(
        core = FluentRuntimeCore(
            path = "bot/resource/locales/{locale}",
        ),
        default_locale = "ru",
    ).setup(dispatcher = admin_bot_manager.dispatcher)

    admin_bot_manager.dispatcher.message.middleware(StringsMiddleware())
    admin_bot_manager.dispatcher.message.middleware(chat_service_middleware)
    admin_bot_manager.dispatcher.message.middleware(
        ReminderServiceMiddleware(),
    )
    admin_bot_manager.dispatcher.message.middleware(
        GetRemindInfoTextScenarioMiddleware(),
    )

    admin_bot_manager.dispatcher.include_router(router = admin_router)

    await admin_bot_manager.start()


if __name__ == '__main__':
    logging.config.dictConfig(get_logging_config())

    asyncio.run(main())
