import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.handlers import router

# Вставьте сюда свой токен
API_TOKEN = 'YOUR_API_TOKEN'


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
