# main.py
import asyncio
import logging
import os
import sys

import ydb
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.di.StringsMiddleware import StringsMiddleware
from bot.domain.get_bot_token import get_bot_token
# Разделяем импорты роутеров для ясности
from bot.entrypoint.business_message_handlers import business_router

# Исправляем импорты на snake_case

# Get the absolute path to the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

async def main():

    if not get_bot_token():
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    dispatcher = Dispatcher()

    I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
        default_locale = "ru",
    ).setup(
        dispatcher = dispatcher
    )
    dispatcher.business_message.middleware(StringsMiddleware())
    dispatcher.business_message.middleware(
        ChatServiceMiddleware()
    )

    bot = Bot(
        token = get_bot_token(),
        default = DefaultBotProperties(parse_mode = "HTML"),
    )

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

    logging.info("Starting bot...")
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
    )
    asyncio.run(main())
