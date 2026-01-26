# main.py

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

load_dotenv()

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types

# Разделяем импорты роутеров для ясности
from bot.handlers import user_router, business_router
from bot.services.firebase_init import init_firebase
from bot.infrastructure.SessionRepository import SessionRepository
from bot.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.ChatService import ChatService


async def main():
    # 2. Инициализация зависимостей (без изменений)
    db_client = init_firebase()
    if db_client is None:
        logging.critical("Failed to initialize Firebase. Exiting.")
        sys.exit(1)

    session_repo = SessionRepository(db=db_client)
    analytics_repo = AnalyticsRepository(db=db_client)
    chat_service = ChatService(session_repo, analytics_repo)

    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    # 3. Настраиваем Dispatcher, внедряя зависимости (без изменений)
    dp = Dispatcher(chat_service=chat_service)
    bot = Bot(token=api_token, parse_mode="HTML")  # Рекомендую HTML для гибкости

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @dp.business_connection()
    async def on_business_connection(connection: types.BusinessConnection):
        """Логирует факт подключения или отключения."""
        conn_id = connection.id
        is_enabled = connection.is_enabled
        user_id = connection.user.id

        if is_enabled:
            logging.info(f"User {user_id} connected business account. Connection ID: {conn_id}")
            # Здесь можно сохранить conn_id в БД, если нужна сложная логика
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
