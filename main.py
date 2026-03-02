# main.py
import asyncio
import locale
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.handlers import MessageHandler
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.feature.admin.entrypoint.handler.handlers import admin_router
from bot.feature.business.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.feature.business.di.StringsMiddleware import StringsMiddleware
from bot.feature.business.domain.get_bot_token import get_bot_token
# Разделяем импорты роутеров для ясности
from bot.feature.business.entrypoint.business_message_handlers import business_router

# Исправляем импорты на snake_case

# Get the absolute path to the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

async def main():

    if not get_bot_token():
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    bot = Bot(
        token = get_bot_token(),
        default = DefaultBotProperties(parse_mode = "HTML"),
    )

    dispatcher = Dispatcher()

    I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
        default_locale = "ru",
    ).setup(
        dispatcher = dispatcher
    )

    setup_business_dispatcher(dispatcher = dispatcher)
    setup_admin_router(dispatcher = dispatcher)

    logging.info("Starting bot...")
    await dispatcher.start_polling(bot)

def setup_business_dispatcher(
    dispatcher: Dispatcher,
):
    dispatcher.business_message.middleware(StringsMiddleware())
    dispatcher.business_message.middleware(ChatServiceMiddleware())

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @dispatcher.business_connection()
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

    dispatcher.include_router(router = business_router)

def setup_admin_router(
    dispatcher: Dispatcher,
):
    dispatcher.include_router(router = admin_router)


if __name__ == '__main__':
    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
    )
    asyncio.run(main())
