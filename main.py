import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers import router
from bot.middlewares.logger import FirestoreLoggingMiddleware
from bot.services.firebase_logger import init_firebase

async def main():
    # 1. Загружаем переменные окружения
    load_dotenv()
    
    # 2. Инициализируем Firebase
    init_firebase()

    # 3. Загружаем токен бота и проверяем его наличие
    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        raise ValueError("Не удалось загрузить токен бота. Проверьте файл .env")

    # 4. Настраиваем Dispatcher и Bot
    bot = Bot(token=api_token)
    dp = Dispatcher()
    
    # 5. Подключаем Middleware для логирования к роутеру
    router.message.middleware(FirestoreLoggingMiddleware())
    
    # 6. Подключаем роутер с хендлерами
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
