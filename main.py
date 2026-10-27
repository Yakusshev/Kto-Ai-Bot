# main.py
import asyncio
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
from dishka import AsyncContainer
from dishka.integrations.aiogram import AiogramProvider, setup_dishka

from bot.core.di.AiogramI18nProvider import AiogramI18nProvider
from bot.core.di.container import create_container
from bot.core.entry.ShutdownSignal import ShutdownSignal
from bot.feature.admin import admin_bot_manager
from bot.feature.admin.entrypoint.handler.admin_handlers import admin_router
from bot.feature.business import user_bot_manager
from bot.feature.business.domain.repository.DelayedTaskQueue import DelayedTaskQueue
from bot.feature.business.entrypoint.business_message_handlers import business_router
from bot.resource.GracefulShutdownFluentRuntimeCore import \
    GracefulShutdownFluentRuntimeCore
from bot.util.log_util import get_logger, get_logging_config
import logging.config


async def main():
    # Ставим обработчики до подключения к YDB, чтобы ранний SIGTERM тоже
    # привёл к штатной остановке
    shutdown_signal = ShutdownSignal()
    shutdown_signal.install(loop = asyncio.get_running_loop())

    container = create_container(
        AiogramProvider(),
        AiogramI18nProvider(),
    )

    try:
        # Драйвер YDB поднимаем сразу: ошибка подключения должна остановить запуск
        await container.get(ydb.SessionPool)

        await start_admin_bot(container)
        await prepare_business_bot(container)

        _logger.info("Бот запущен, ожидаю SIGTERM/SIGINT для остановки")
        await shutdown_signal.wait()
    finally:
        await shutdown(container = container)


async def shutdown(
    container: AsyncContainer,
) -> None:
    """Штатная остановка: новые сообщения не принимаем, текущие ответы дописываем."""
    _logger.info("Остановка: прекращаю приём новых сообщений")
    await admin_bot_manager.stop()
    await user_bot_manager.stop()

    # Покрывает и ответы бизнес-бота, и напоминания из админ-бота: запущенные шаги
    # дописываются, не начатые отбрасываются (в SQS они остались бы в очереди)
    _logger.info("Остановка: жду завершения запущенных шагов")
    await (await container.get(DelayedTaskQueue)).shutdown()

    await admin_bot_manager.close()
    await user_bot_manager.close()

    # Закрывает session pool и driver YDB (в порядке, обратном созданию)
    await container.close()
    _logger.info("Остановка завершена")


async def prepare_business_bot(
    container: AsyncContainer,
):
    i18n = I18nMiddleware(
        core = GracefulShutdownFluentRuntimeCore(
            path = "bot/resource/locales/{locale}",
        ),
        default_locale = "ru",
    )
    i18n.setup(dispatcher = user_bot_manager.dispatcher)

    # После i18n: Strings берёт I18nContext из data апдейта
    setup_dishka(
        container = container,
        router = user_bot_manager.dispatcher,
        auto_inject = True,
    )

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
    container: AsyncContainer,
):
    I18nMiddleware(
        core = FluentRuntimeCore(
            path = "bot/resource/locales/{locale}",
        ),
        default_locale = "ru",
    ).setup(dispatcher = admin_bot_manager.dispatcher)

    setup_dishka(
        container = container,
        router = admin_bot_manager.dispatcher,
        auto_inject = True,
    )

    admin_bot_manager.dispatcher.include_router(router = admin_router)

    await admin_bot_manager.start()


_logger = get_logger("main")


if __name__ == '__main__':
    logging.config.dictConfig(get_logging_config())

    asyncio.run(main())
