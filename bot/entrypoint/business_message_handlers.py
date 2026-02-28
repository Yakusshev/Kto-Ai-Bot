# bot/business_message_handlers.py
import asyncio
import logging
import random
import traceback
from asyncio import Task
from venv import logger

from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.entrypoint.ChatService import ChatService
from bot.entrypoint.HumanWaitingBehavior import wait_to_see_message, \
    wait_to_start_typing, wait_to_write_message
from bot.resource.Strings import Strings

business_router = Router()


# TODO фильтер на юзер id - чтобы бот работал только на моих аккаунтах
@business_router.business_message(F.text)
async def __handle_text(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
):
    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = message.text,
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = strings.sticker_not_loaded(emoji = message.sticker.emoji),
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
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
    )


@business_router.business_message(F.voice)
async def __handle_voice_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    text_content = strings.voice_message_cannot_be_loaded(
        user = message.from_user.full_name,
    )

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
    )


@business_router.business_message(F.video_note)
async def __handle_voice_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    text_content = strings.video_message_cannot_be_loaded(
        user = message.from_user.full_name,
    )

    await __handle_message(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = text_content,
    )


async def __handle_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
):
    print(
        "handle_business_message text_content = ", text_content,
        "; ", message,
    )

    message_from_user_id = message.from_user.id
    message_chat_id = message.chat.id

    if (
        message_from_user_id == message_chat_id
        and message.business_connection_id
    ):

        try:
            scheduler = TaskSchedulerRepositoryImpl()
            task_key = str(message.chat.id)

            await scheduler.handle(
                key = task_key,
                prepare = _prepare_for_answer(
                    message = message,
                    bot = bot,
                    chat_service = chat_service,
                    text_content = text_content,
                ),
                answer = scheduler.schedule_answering_task(
                    key = task_key,
                    coroutine = __answer_message(
                        bot = bot,
                        chat_service = chat_service,
                        text_content = text_content,
                        message_chat_id = message_chat_id,
                        user_name = message.from_user.username,
                        business_connection_id = message.business_connection_id,
                    ),
                ),
            )

        except asyncio.CancelledError:
            logger.info(
                f"handle_business_message {text_content} cancelled; message = {message}",
            )
            raise
    else:
        print(
            f"Сообщение не было обработано"
            f"message.from_user.id[{message_from_user_id}] != message.chat.id[{message_chat_id}]"
            f"message.business_connection_id = {message.business_connection_id}",
        )


async def _prepare_for_answer(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
):
    message_chat_id = message.chat.id

    scheduler = TaskSchedulerRepositoryImpl()
    task_key = str(message.chat.id)

    await chat_service.save_message_model(
        message = message,
        text_content = text_content,
    )

    await scheduler.cancel_or_await(key = task_key)

    if not scheduler.has_task(key = task_key):
        await wait_to_see_message()

    await bot.read_business_message(
        business_connection_id = message.business_connection_id,
        chat_id = message_chat_id,
        message_id = message.message_id,
    )


async def __answer_message(
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
    message_chat_id: int,
    user_name: str,
    business_connection_id: str,
):
    stop_typing = None
    typing_task = None

    answer_message_list: list[Message] = []

    try:
        await wait_to_start_typing(message = text_content)

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            __typing_loop(
                bot = bot,
                chat_id = message_chat_id,
                business_connection_id = business_connection_id,
                stop_event = stop_typing,
            ),
        )

        ai_answer_list = await chat_service.generate_ai_response(
            message_chat_id = message_chat_id,
            user_name = user_name,
        )

        for ai_answer in ai_answer_list:
            await wait_to_write_message(ai_answer)

            answer_message = await bot.send_message(
                chat_id = message_chat_id,
                text = ai_answer,
                business_connection_id = business_connection_id,
            )

            answer_message_list.append(answer_message)

    except asyncio.CancelledError as e:
        logger.info(f"__answer_message {text_content} cancelled;")
        raise
    finally:

        await chat_service.handle_self_message(message_list = answer_message_list)

        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


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
