import asyncio
import logging
import sys
from multiprocessing.util import DEBUG

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.filters import Command
from bot.services.ChatService import ChatService

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я мешок слов. Задавай вопросы")

@router.message(F.text)
async def handle_message(message: Message, bot: Bot, chat_service: ChatService):
    """
    Основной обработчик, делегирующий всю работу в ChatService.
    """
    local_logger = logging.getLogger("handle_message")
    local_logger.setLevel(DEBUG)

    local_logger.debug("message handle started")

    asyncio.create_task(
        bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING,
        )
    )

    local_logger.debug("action TYPING sent")

    response_text = await chat_service.handle_user_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        text=message.text
    )

    local_logger.debug("response_text is ready")

    await message.answer(response_text)
