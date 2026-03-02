import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

from bot.feature.admin.entrypoint.filter.IsAdminUserFilter import IsAdminUserFilter
from bot.feature.business import user_bot_manager

logger = logging.getLogger("admin_handler")
admin_router = Router()


@admin_router.message(Command("stop"), IsAdminUserFilter())
async def __handle_stop(
    message: Message,
    bot: Bot,
):
    logger.info(f"Handling stop command: {message}")

    result = await user_bot_manager.stop()

    await bot.send_message(
        chat_id = message.chat.id,
        text = f"Stop result is {result}",
    )


@admin_router.message(Command("start"), IsAdminUserFilter())
async def __handle_start(
    message: Message,
    bot: Bot,
):
    logger.info(f"Handling start command: {message}")

    result = await user_bot_manager.start()

    await bot.send_message(
        chat_id = message.chat.id,
        text = f"Start result is {result}",
    )
