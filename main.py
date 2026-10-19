# main.py
import asyncio
import locale
import logging
import sys

from bot.core.config.ConfigError import ConfigError

# Конфиг проверяется первым: при ошибке печатаем список проблем без трейсбека
try:
    from bot.core.domain.const.env_const import DEBUG_MODE_START_POLLING
except ConfigError as config_error:
    sys.exit(f"{config_error}")

import ydb
from aiogram import types
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.core.entry.ShutdownSignal import ShutdownSignal
from bot.feature.admin import admin_bot_manager
from bot.feature.admin.di.ReminderServiceMiddleware import ReminderServiceMiddleware
from bot.feature.admin.entrypoint.handler.admin_handlers import admin_router
from bot.feature.business import user_bot_manager
from bot.feature.business.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.feature.business.di.StringsMiddleware import StringsMiddleware
from bot.feature.business.entrypoint.business_message_handlers import business_router
from bot.resource.GracefulShutdownFluentRuntimeCore import \
    GracefulShutdownFluentRuntimeCore
from bot.util.log_util import get_logger, get_logging_config
import logging.config
from bot.feature.admin.di.GetRemindInfoTextScenarioMiddleware import \
    GetRemindInfoTextScenarioMiddleware


async def main():
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    # Ставим обработчики до подключения к YDB, чтобы ранний SIGTERM тоже
    # привёл к штатной остановке
    shutdown_signal = ShutdownSignal()
    shutdown_signal.install(loop = asyncio.get_running_loop())

    driver = create_ydb_driver()
    ydb_session_pool = ydb.SessionPool(driver)

    try:
        chat_service_middleware = ChatServiceMiddleware(
            driver = driver,
            ydb_session_pool = ydb_session_pool,
        )

        await start_admin_bot(chat_service_middleware)
        await prepare_business_bot(chat_service_middleware)

        _logger.info("Бот запущен, ожидаю SIGTERM/SIGINT для остановки")
        await shutdown_signal.wait()
    finally:
        await shutdown(
            driver = driver,
            ydb_session_pool = ydb_session_pool,
        )


async def shutdown(
    driver: ydb.Driver,
    ydb_session_pool: ydb.SessionPool,
) -> None:
    """Штатная остановка: новые сообщения не принимаем, текущие ответы дописываем."""
    _logger.info("Остановка: прекращаю приём новых сообщений")
    await admin_bot_manager.stop()
    await user_bot_manager.stop()

    # Покрывает и ответы бизнес-бота, и напоминания, запущенные из админ-бота
    _logger.info("Остановка: жду завершения ответов в процессе")
    await TaskSchedulerRepositoryImpl().wait_task_completion()

    await admin_bot_manager.close()
    await user_bot_manager.close()

    await asyncio.to_thread(ydb_session_pool.stop)
    await asyncio.to_thread(driver.stop)
    _logger.info("Остановка завершена")


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


_logger = get_logger("main")


if __name__ == '__main__':
    logging.config.dictConfig(get_logging_config())

    asyncio.run(main())
