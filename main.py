# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher

from bot.handlers import router
# Обновленный импорт
from bot.services.firebase_init import init_firebase
from bot.infrastructure.SessionRepository import SessionRepository
from bot.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.ChatService import ChatService

async def main():

    logging.basicConfig(
        force = True,
        level=logging.DEBUG,  # <--- Самое важное: разрешаем DEBUG
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Явно указываем вывод в консоль
        ],
        datefmt="%H:%M:%S",
    )

    # 2. Инициализируем Firebase и получаем клиент БД
    db_client = init_firebase()
    if db_client is None:
        logging.critical("Failed to initialize Firebase. Exiting.")
        sys.exit(1)

    # 3. Инициализируем репозитории, передавая им клиент БД
    session_repo = SessionRepository(db=db_client)
    analytics_repo = AnalyticsRepository(db=db_client)
    
    # 4. Инициализируем сервис, передавая ему репозитории
    chat_service = ChatService(session_repo, analytics_repo)

    # 5. Загружаем токен бота
    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        logging.critical("BOT_TOKEN not found. Exiting.")
        sys.exit(1)

    # 6. Настраиваем Dispatcher, внедряя chat_service
    dp = Dispatcher(chat_service=chat_service)
    bot = Bot(token=api_token)
    
    dp.include_router(router)
    
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
