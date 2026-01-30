# bot/handlers.py
import asyncio
import random
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

from bot.domain.const.env_const import DEBUG_MODE
# Исправленный импорт в соответствии с вашим стилем
from bot.services.ChatService import ChatService

# --- Роутер для бизнес-сообщений ---
business_router = Router()

# убрать делеи, разобраться с message quee
@business_router.business_message(F.text)
async def handle_business_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService
):
    """
    Обрабатывает сообщения, приходящие через Telegram Business.
    """

    print("handle_business_message ", message.text, "; ", message)

    if not message.business_connection_id:
        return

    chat_id = message.chat.id

    # ping = datetime.now(message.text) - message.date

    if message.from_user.id == message.chat.id:

        response_text_coroutine = chat_service.handle_user_message(
            message = message,
            user_id = chat_id,
            text = message.text
        )

        if not DEBUG_MODE:
            await asyncio.sleep(random.uniform(1, 4))

        await bot.read_business_message(
            business_connection_id = message.business_connection_id,
            chat_id = chat_id,
            message_id = message.message_id,
        )

        if not DEBUG_MODE:
            read_time = len(message.text.split()) / 3.5
            await asyncio.sleep(read_time)

        await bot.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = message.business_connection_id
        )

        response_text = await response_text_coroutine

        if not DEBUG_MODE:
            write_time = len(response_text) / 10
            await asyncio.sleep(write_time)

        answer_message = await bot.send_message(
            chat_id = chat_id,
            text = response_text,
            business_connection_id = message.business_connection_id
        )

        await chat_service.handle_self_message(message = answer_message)
    else:
        # TODO рассмотреть возможность записывать ответ на сообщение во время отправки ответа
        await chat_service.handle_self_message(message = message)
