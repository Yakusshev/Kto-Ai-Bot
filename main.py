# main.py
import asyncio
import locale
import logging

from aiogram import Dispatcher, types
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.feature.admin import admin_bot_manager
from bot.feature.admin.entrypoint.handler.handlers import admin_router
from bot.feature.business import user_bot_manager
from bot.feature.business.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.feature.business.di.StringsMiddleware import StringsMiddleware
from bot.feature.business.entrypoint.business_message_handlers import business_router


async def main():
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    await start_user_dispatcher_polling_task()
    await start_admin_dispatcher_polling_task()

    await asyncio.Future()


async def start_user_dispatcher_polling_task():
    I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
        default_locale = "ru",
    ).setup(
        dispatcher = user_bot_manager.dispatcher,
    )
    user_bot_manager.dispatcher.business_message.middleware(StringsMiddleware())

    setup_business_router()

    await user_bot_manager.start()


def setup_business_router():
    user_bot_manager.dispatcher.business_message.middleware(ChatServiceMiddleware())

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


async def start_admin_dispatcher_polling_task():
    I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
        default_locale = "ru",
    ).setup(
        dispatcher = admin_bot_manager.dispatcher,
    )
    admin_bot_manager.dispatcher.message.middleware(StringsMiddleware())

    admin_bot_manager.dispatcher.include_router(router = admin_router)

    await admin_bot_manager.start()


if __name__ == '__main__':
    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
    )
    asyncio.run(main())
