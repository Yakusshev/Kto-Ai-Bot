import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

from bot.core.domain.const.env_const import ADMIN_ID_LIST
from bot.feature.admin.entrypoint.filter.IsAdminUserFilter import IsAdminUserFilter

logger = logging.getLogger("admin_handler")
admin_router = Router()


@admin_router.message(Command("stop"), IsAdminUserFilter)
async def __handle_text(
    message: Message,
):
    logger.info(f"Handling message: ADMIN_ID_LIST = {ADMIN_ID_LIST}")
    logger.info(f"Handling message: {message}")