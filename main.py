# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher

from bot.handlers import router
from bot.services.firebase_logger import init_firebase
from bot.infrastructure.session_repo import SessionRepository
from bot.infrastructure.analytics_repo import AnalyticsRepository
from bot.services.chat_service import ChatService

async def main():
    # 2. Инициализируем Firebase
    init_firebase()

    # 3. Инициализируем репозитории и сервисы (Composition Root)
    session_repo = SessionRepository()
    analytics_repo = AnalyticsRepository()
    chat_service = ChatService(session_repo, analytics_repo)

    # 4. Загружаем токен бота
    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        raise ValueError("Не удалось загрузить токен бота. Проверьте файл .env")

    # 5. Настраиваем Dispatcher и Bot, внедряя зависимости
    dp = Dispatcher(chat_service=chat_service)
    bot = Bot(token=api_token)
    
    # 6. Подключаем роутер
    dp.include_router(router)
    
    # 7. Запускаем поллинг
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
    except ValueError as e:
        print(e)
