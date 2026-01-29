# bot/handlers.py

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

# Исправленный импорт в соответствии с вашим стилем
from bot.services.ChatService import ChatService

# --- Роутер для бизнес-сообщений ---
business_router = Router()

@business_router.business_message(F.text)
async def handle_business_message(message: Message, bot: Bot, chat_service: ChatService):
    """
    Обрабатывает сообщения, приходящие через Telegram Business.
    """

    print("handle_business_message ", message.text, "; ", message)

    if not message.business_connection_id:
        return

    chat_id = message.chat.id

    if message.from_user.id == message.chat.id:

        await bot.send_chat_action(
            chat_id=chat_id,
            action="typing",
            business_connection_id=message.business_connection_id
        )

        response_text = await chat_service.handle_user_message(
            message = message,
            user_id=chat_id,
            username=message.chat.full_name,
            text=message.text
        )

        await bot.send_message(
            chat_id=chat_id,
            text=response_text,
            business_connection_id=message.business_connection_id
        )
    else:
        #TODO рассмотреть возможность записывать ответ на сообщение во время отправки ответа
        await chat_service.handle_self_message(
            message = message,
        )


