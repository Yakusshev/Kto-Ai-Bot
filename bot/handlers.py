import os
from dotenv import load_dotenv

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from bot.services.gemini import generate_response

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
    await message.answer("Привет! Я Gemini Proxy бот. Просто отправь мне свой вопрос.")


async def send_with_markdown_fallback(message: Message, text: str):
    """
    Пытается отправить сообщение с MarkdownV2, и если не получается,
    отправляет как обычный текст.
    """
    try:
        await message.answer(text, parse_mode="MarkdownV2")
    except TelegramBadRequest:
        # Если разметка некорректна, отправляем без нее
        await message.answer(text)


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """
    Разбивает длинный текст на части, не превышающие max_length.
    Старается разбивать по переносам строк или пробелам.
    """
    parts = []
    while len(text) > 0:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        # Ищем ближайший перенос строки или пробел для разрыва
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        
        if split_pos == -1: # Если не нашли, режем как есть
            split_pos = max_length
            
        parts.append(text[:split_pos])
        # Обрезаем отправленную часть, удаляя пробел/перенос в начале следующей части
        text = text[split_pos:].lstrip() 
        
    return parts


@router.message(F.text)
async def handle_message(message: Message, bot: Bot):
    """
    Основной обработчик текстовых сообщений.
    """
    # 1. Отправляем статус "печатает"
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        await message.answer("⚠ API-ключ для Gemini не настроен.")
        return

    try:
        # 2. Получаем ответ от Gemini
        prompt = message.text
        ai_response = await generate_response(prompt, gemini_api_key)

        # Проверяем, не вернул ли сервис свою ошибку
        if ai_response == "Ошибка обращения к AI":
             await message.answer("⚠ Произошла ошибка при обращении к нейросети. Попробуйте позже.")
             return

    except Exception as e:
        # Логируем ошибку и сообщаем пользователю
        print(f"Ошибка при генерации ответа: {e}")
        await message.answer("⚠ Произошла ошибка при обращении к нейросети. Попробуйте позже.")
        return

    # 3. Нарезаем и отправляем ответ
    if len(ai_response) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        # Если сообщение короткое, отправляем как есть
        await send_with_markdown_fallback(message, ai_response)
    else:
        # Если длинное, режем на части
        parts = split_long_message(ai_response)
        for part in parts:
            await send_with_markdown_fallback(message, part)
