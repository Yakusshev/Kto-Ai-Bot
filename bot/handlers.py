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
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    response_text = await chat_service.handle_user_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        text=message.text
    )
    
    await message.answer(response_text)
