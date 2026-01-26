# bot/handlers.py

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

# Исправленный импорт в соответствии с вашим стилем
from bot.services.ChatService import ChatService

# --- Роутер для обычных сообщений (в личке бота) ---
user_router = Router()

@user_router.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик команды /start для обычного чата."""
    await message.answer(
        "Привет! Я ваш AI-ассистент. Просто напишите мне.\\n\\n"
        "Чтобы я отвечал на сообщения в ваших личных чатах, "
        "подключите меня в Настройках > Telegram Business."
    )

@user_router.message(F.text, ~F.business)  # Фильтр ~F.business ОБЯЗАТЕЛЕН!
async def handle_user_message(message: Message, bot: Bot, chat_service: ChatService):
    """
    Обрабатывает обычные сообщения, отправленные боту напрямую.
    """
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    response_text = await chat_service.handle_user_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        text=message.text
    )
    
    await message.answer(response_text)


# --- Роутер для бизнес-сообщений ---
business_router = Router()

@business_router.business_message(F.text)
async def handle_business_message(message: Message, bot: Bot, chat_service: ChatService):
    """
    Обрабатывает сообщения, приходящие через Telegram Business.
    """
    # ГЛАВНАЯ ПРОВЕРКА: бот отвечает только на сообщения клиента, а не на свои или владельца.
    if message.from_user.id != message.chat.id:
        return # Игнорируем сообщение

    user_id = message.chat.id
    
    if not message.business_connection_id:
        return

    await bot.send_chat_action(
        chat_id=user_id,
        action="typing",
        business_connection_id=message.business_connection_id
    )

    response_text = await chat_service.handle_user_message(
        user_id=user_id,
        username=message.chat.full_name,
        text=message.text
    )
    
    await bot.send_message(
        chat_id=user_id,
        text=response_text,
        business_connection_id=message.business_connection_id
    )
