import os
import time
from dotenv import load_dotenv

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from bot.services.gemini import generate_response
from bot.services.analytics import analytics # Импортируем сервис аналитики

# Загружаем переменные окружения
load_dotenv()

router = Router()

# Константа для длины сообщения
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Обработчик команды /start.
    """
    user_id = message.from_user.id
    await analytics.log_event(user_id, "command_use", {"command": "start"})
    await message.answer("Привет! Я Gemini Proxy бот. Просто отправь мне свой вопрос.")


async def send_with_markdown_fallback(message: Message, text: str):
    """
    Пытается отправить сообщение с MarkdownV2, и если не получается,
    отправляет как обычный текст.
    """
    try:
        await message.answer(text, parse_mode="MarkdownV2")
    except TelegramBadRequest:
        await message.answer(text)


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """
    Разбивает длинный текст на части.
    """
    parts = []
    while len(text) > 0:
        if len(text) <= max_length:
            parts.append(text)
            break
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()
    return parts


@router.message(F.text)
async def handle_message(message: Message, bot: Bot):
    """
    Основной обработчик текстовых сообщений.
    """
    user_id = message.from_user.id
    start_time = time.time()

    # Аналитика: начало обработки запроса
    await analytics.log_event(user_id, "ai_request", {
        "model": "gemini-pro", # или другая ваша модель
        "input_chars": len(message.text)
    })

    await bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        await message.answer("⚠ API-ключ для Gemini не настроен.")
        return

    try:
        prompt = message.text
        ai_response = await generate_response(prompt, gemini_api_key)

        if ai_response == "Ошибка обращения к AI":
            await analytics.log_event(user_id, "ai_error", {"error_type": "ServiceError"})
            await message.answer("⚠ Произошла ошибка при обращении к нейросети. Попробуйте позже.")
            return

    except Exception as e:
        # Аналитика: ошибка при генерации
        await analytics.log_event(user_id, "ai_error", {"error_type": type(e).__name__})
        print(f"Ошибка при генерации ответа: {e}")
        await message.answer("⚠ Произошла ошибка при обращении к нейросети. Попробуйте позже.")
        return

    # Аналитика: успешный ответ
    duration = time.time() - start_time
    await analytics.log_event(user_id, "ai_complete", {
        "duration_sec": round(duration, 2),
        "output_chars": len(ai_response)
    })

    if len(ai_response) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        await send_with_markdown_fallback(message, ai_response)
    else:
        parts = split_long_message(ai_response)
        for part in parts:
            await send_with_markdown_fallback(message, part)
