# bot/business_message_handlers.py
import asyncio
import random

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram_i18n import I18nContext

from bot.domain.const.env_const import DEBUG_MODE
from bot.entrypoint.ChatService import ChatService
from bot.entrypoint.HumanWaitingBehavior import wait_to_see_message, \
    wait_to_read_message, wait_to_write_message
from bot.resource.Strings import Strings

business_router = Router()


@business_router.business_message(F.text)
async def __handle_text(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = message.text,
        strings = Strings(i18n = i18n),
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    strings = Strings(i18n = i18n)

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = strings.sticker_not_loaded(emoji = message.sticker.emoji),
        strings = strings,
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    strings = Strings(i18n = i18n)

    text_content: str

    if len(message.photo) > 1 and message.text is not None:
        text_content = strings.photo_list_cannot_be_loaded_text(
            user = message.from_user.full_name,
            photo_number = len(message.photo),
            text = message.text,
        )
    elif len(message.photo) > 1:
        text_content = strings.photo_list_cannot_be_loaded(
            user = message.from_user.full_name,
            photo_number = len(message.photo),
        )
    elif message.text is not None:
        text_content = strings.photo_cannot_be_loaded_text(
            user = message.from_user.full_name,
            text = message.text,
        )
    else:
        text_content = strings.photo_cannot_be_loaded(
            user = message.from_user.full_name,
        )

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
        strings = Strings(i18n = i18n),
    )


@business_router.business_message(F.voice)
async def __handle_voice_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    strings = Strings(i18n = i18n)

    text_content = strings.voice_message_cannot_be_loaded(
        user = message.from_user.full_name,
    )

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
        strings = Strings(i18n = i18n),
    )


@business_router.business_message(F.video_note)
async def __handle_voice_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    strings = Strings(i18n = i18n)

    text_content = strings.video_message_cannot_be_loaded(
        user = message.from_user.full_name,
    )

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
        strings = strings,
    )


async def __handle_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
    strings: Strings,
):
    print(
        "handle_business_message text_content = ", text_content,
        "message.text = ", message.text, "; ", message,
    )

    if message.from_user.id == message.chat.id and message.business_connection_id:

        await wait_to_see_message()

        await bot.read_business_message(
            business_connection_id = message.business_connection_id,
            chat_id = message.chat.id,
            message_id = message.message_id,
        )

        await wait_to_read_message(message = text_content)

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            __typing_loop(
                bot = bot,
                chat_id = message.chat.id,
                business_connection_id = message.business_connection_id,
                stop_event = stop_typing,
            ),
        )

        try:
            ai_answer_list = await chat_service.handle_user_text_message(
                message = message,
                content = text_content,
                strings = strings,
            )

            for ai_answer in ai_answer_list:
                await wait_to_write_message(ai_answer)

                answer_message = await bot.send_message(
                    chat_id = message.chat.id,
                    text = ai_answer,
                    business_connection_id = message.business_connection_id,
                )
                await chat_service.handle_self_message(
                    message = answer_message,
                    strings = strings,
                )
        finally:
            # --- останавливаем typing в любом случае (даже при ошибке) ---
            stop_typing.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

    else:
        print(
            f"Сообщение не было обработано"
            f"message.from_user.id[{message.from_user.id}] != message.chat.id[{message.chat.id}]"
            f"message.business_connection_id = {message.business_connection_id}",
        )


# TODO убрать делеи, разобраться с message quee
async def __typing_loop(
    bot: Bot,
    chat_id: int,
    business_connection_id: str,
    stop_event: asyncio.Event,
):
    """Поддерживает typing indicator всё время, пока не выставлен stop_event.
    Иногда делает паузу 1–3 сек (имитирует "задумался")."""
    while not stop_event.is_set():
        await bot.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = business_connection_id,
        )
        # typing живёт ~5 сек — обновляем каждые 4 сек,
        # но иногда делаем случайную паузу (1–3 сек), из-за которой он ненадолго гаснет
        base_interval = 4.0
        if random.random() < 0.32:
            pause = random.uniform(1.0, 3.0)
            await asyncio.sleep(pause)
        else:
            await asyncio.sleep(base_interval)
