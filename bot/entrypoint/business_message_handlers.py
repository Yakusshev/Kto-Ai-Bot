# bot/business_message_handlers.py
import asyncio
import logging
import random

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram_i18n import I18nContext

from bot.domain.const.env_const import DEBUG_MODE
from bot.entrypoint.ChatService import ChatService
from main import logger

business_router = Router()


@business_router.business_message(F.text)
async def __handle_text(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext
):
    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = message.text,
        i18n = i18n
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext
):
    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = i18n.get('sticker-not-loaded', emoji = message.sticker.emoji),
        i18n = i18n
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext
):
    if message.photo:
        if len(message.photo) > 1:
            text_content = i18n.get('photo-list-cannot-be-loaded', user = message.from_user.full_name)
        else:
            text_content = i18n.get('photo-cannot-be-loaded', user = message.from_user.full_name)
    else:
        text_content = ""

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
        i18n = i18n
    )


# TODO убрать делеи, разобраться с message quee
async def __handle_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
    i18n: I18nContext
):
    logger.debug("handle_business_message text_content = ", text_content, "message.text = ", message.text, "; ",
                 message)

    if not message.business_connection_id:
        return

    chat_id = message.chat.id

    if message.from_user.id == message.chat.id:

        response_text_coroutine = chat_service.handle_user_text_message(
            message = message,
            content = text_content,
            i18n = i18n
        )

        if not DEBUG_MODE:
            await asyncio.sleep(random.uniform(1, 4))

        await bot.read_business_message(
            business_connection_id = message.business_connection_id,
            chat_id = chat_id,
            message_id = message.message_id,
        )

        if not DEBUG_MODE:
            read_time = len(text_content.split()) / 2.5
            await asyncio.sleep(read_time)

        await bot.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = message.business_connection_id
        )

        ai_answer_list = await response_text_coroutine

        for _, ai_answer in enumerate(ai_answer_list):

            if not DEBUG_MODE:
                write_time = len(ai_answer) / random.uniform(a = 3, b = 10)
                await asyncio.sleep(delay = write_time)

            ##TODO async
            answer_message = await bot.send_message(
                chat_id = chat_id,
                text = ai_answer,
                business_connection_id = message.business_connection_id
            )
            await chat_service.handle_self_message(message = answer_message)

    else:
        print(f"message.from_user.id[{message.from_user.id}] != message.chat.id[{message.chat.id}]")
        # TODO рассмотреть возможность записывать ответ на сообщение во время отправки ответа
        await chat_service.handle_self_message(message = message)
