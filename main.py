# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher

from bot.handlers import router
from bot.middlewares.FirestoreLoggingMiddleware import FirestoreLoggingMiddleware
from bot.services.firebase_logger import init_firebase
# Импортируем КЛАСС
from bot.services.GoogleAnalyticsService import GoogleAnalyticsService

async def main():
    # 2. Инициализируем сервисы
    init_firebase()
    # Создаем экземпляр сервиса аналитики здесь, ПОСЛЕ load_dotenv()
    analytics_service = GoogleAnalyticsService()

    # 3. Загружаем токен бота
    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        raise ValueError("Не удалось загрузить токен бота. Проверьте файл .env")

    # 4. Настраиваем Dispatcher и Bot
    # Передаем созданный сервис в DI-контейнер диспетчера
    dp = Dispatcher(analytics=analytics_service)
    bot = Bot(token=api_token)
    
    # 5. Подключаем Middleware
    router.message.middleware(FirestoreLoggingMiddleware())
    
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
