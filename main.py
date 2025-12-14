import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers import router

async def main():
    load_dotenv()
    # Загружаем токен из переменных окружения
    api_token = os.getenv("BOT_TOKEN")
    if not api_token:
        raise ValueError("Не удалось загрузить токен бота. Проверьте файл .env")

    bot = Bot(token=api_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
    except ValueError as e:
        print(e)
