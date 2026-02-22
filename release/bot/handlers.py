# bot/handlers.py
import asyncio
import random

from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.domain.const.env_const import DEBUG_MODE
from bot.resource.string.dynamic_strings import dynamic_string_sticker_emoji
from bot.services.ChatService import ChatService

business_router = Router()


@business_router.business_message(F.text)
async def handle_business_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService
):
    await handle_business_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = message.text,
    )


@business_router.business_message(F.sticker)
async def handle_business_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService
):
    await handle_business_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = dynamic_string_sticker_emoji(message.sticker.emoji),
    )


# убрать делеи, разобраться с message quee
async def handle_business_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
):
    print("handle_business_message text_content = ", text_content, "message.text = ", message.text, "; ", message)

    if not message.business_connection_id:
        return

    chat_id = message.chat.id

    if message.from_user.id == message.chat.id:

        response_text_coroutine = chat_service.handle_user_message(
            message = message,
            content = text_content,
        )

        if not DEBUG_MODE:
            await asyncio.sleep(random.uniform(1, 4))

        await bot.read_business_message(
            business_connection_id = message.business_connection_id,
            chat_id = chat_id,
            message_id = message.message_id,
        )

        if not DEBUG_MODE:
            read_time = len(text_content.split()) / 3.5
            await asyncio.sleep(read_time)

        await bot.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = message.business_connection_id
        )

        ai_answer_list = await response_text_coroutine

        if not DEBUG_MODE:
            write_time = len(" ".join(ai_answer_list)) / 10
            await asyncio.sleep(write_time)

        for i, ai_answer in enumerate(ai_answer_list):
            ##TODO async
            answer_message = await bot.send_message(
                chat_id = chat_id,
                text = ai_answer,
                business_connection_id = message.business_connection_id
            )
            await chat_service.handle_self_message(message = answer_message)

    else:
        # TODO рассмотреть возможность записывать ответ на сообщение во время отправки ответа
        await chat_service.handle_self_message(message = message)

