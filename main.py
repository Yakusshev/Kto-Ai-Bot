# main.py
import ydb
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.di.llm_module import get_llm_repository
from bot.domain.const.env_const import TELEGRAM_BOT_TOKEN

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties

from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
# Разделяем импорты роутеров для ясности
from bot.entrypoint.business_message_handlers import business_router
# Исправляем импорты на snake_case
from bot.data.repository.SessionRepository import SessionRepository
from bot.entrypoint.ChatService import ChatService



async def main():
    driver = create_ydb_driver()
    ydb_session_pool = ydb.SessionPool(driver)

    session_repository = SessionRepository(ydb_session_pool = ydb_session_pool)

    chat_service = ChatService(
        generate_ai_response_use_case = GenerateAiResponseUseCase(
            session_repository = session_repository,
            llm_repository = get_llm_repository(),
        ),
        save_message_use_case = SaveMessageUseCase(session_repository = session_repository),
    )

    if not TELEGRAM_BOT_TOKEN:
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    # 3. Настраиваем Dispatcher и Bot
    dispatcher = Dispatcher(chat_service = chat_service)

    i18n_middleware = I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/locales/{locale}"),
        default_locale = "ru"
    )
    i18n_middleware.setup(dispatcher)

    bot = Bot(
        token = TELEGRAM_BOT_TOKEN,
        default = DefaultBotProperties(parse_mode = "HTML")
    )

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @dispatcher.business_connection()
    async def on_business_connection(connection: types.BusinessConnection):
        """Логирует факт подключения или отключения."""
        conn_id = connection.id
        is_enabled = connection.is_enabled
        user_id = connection.user.id

        if is_enabled:
            logging.info(f"User {user_id} connected business account. Connection ID: {conn_id}")
        else:
            logging.warning(f"User {user_id} DISABLED business account. Connection ID: {conn_id}")

    dispatcher.include_router(router = business_router)

    logging.info("Starting bot...")
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
    )
    asyncio.run(main())

