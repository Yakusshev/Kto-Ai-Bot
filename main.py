# main.py
import ydb

from bot.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.domain.const.env_const import TELEGRAM_BOT_TOKEN
from bot.services.llm_service import get_llm_client

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties

# Разделяем импорты роутеров для ясности
from bot.handlers import user_router, business_router
from bot.services.firebase_init import init_firebase
# Исправляем импорты на snake_case
from bot.data.infrastructure.SessionRepository import SessionRepository
from bot.data.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.ChatService import ChatService

async def main():
    # 2. Инициализация зависимостей

    driver = create_ydb_driver()
    ydb_session_pool = ydb.SessionPool(driver)

    db_client = init_firebase()
    if db_client is None:
        logging.critical("Failed to initialize Firebase. Exiting.")
        sys.exit(1)

    session_repo = SessionRepository(ydb_session_pool = ydb_session_pool)
    analytics_repo = AnalyticsRepository(db=db_client)
    chat_service = ChatService(session_repo, analytics_repo, get_llm_client())

    if not TELEGRAM_BOT_TOKEN:
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    # 3. Настраиваем Dispatcher и Bot
    dp = Dispatcher(chat_service=chat_service)
    
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @dp.business_connection()
    async def on_business_connection(connection: types.BusinessConnection):
        """Логирует факт подключения или отключения."""
        conn_id = connection.id
        is_enabled = connection.is_enabled
        user_id = connection.user.id

        if is_enabled:
            logging.info(f"User {user_id} connected business account. Connection ID: {conn_id}")
        else:
            logging.warning(f"User {user_id} DISABLED business account. Connection ID: {conn_id}")

    # 5. Подключаем ОБА роутера
    dp.include_router(user_router)
    dp.include_router(business_router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main())
